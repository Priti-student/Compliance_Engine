"""Inspection orchestration: engine scan -> persistence -> report artifacts."""
from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.engine_client import engine_client
from app.core.exceptions import BadRequest, EngineUnavailable
from app.core.storage import Storage
from app.models.inspection import Inspection
from app.models.user import User
from app.schemas.inspection import InspectionMeta
from app.services.report_loader import (
    FIELD_GENERIC_NAME,
    apply_compliance_report,
    upsert_product,
)


def _now_utc_str() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _engine_metadata(meta: InspectionMeta, user: User, token: str) -> dict:
    return {
        "scan_id": token,
        "officer": user.username,
        "product_name": meta.product_name,
        "product_category": meta.category,
        "package_flagged_as_imported": meta.package_flagged_as_imported,
        "enforce_unit_sale_price": meta.enforce_unit_sale_price,
        "brand": meta.brand,
        "manufacturer": meta.manufacturer,
    }


async def create_inspection(
    db: Session,
    user: User,
    storage: Storage,
    image_bytes: bytes,
    filename: str,
    content_type: str,
    meta: InspectionMeta,
) -> Inspection:
    """Run the engine scan and persist image, report rows and artifacts."""
    token = secrets.token_hex(8)
    safe_name = Path(filename).name or "upload.jpg"
    image_key = f"inspections/{token}/{safe_name}"

    storage.save(image_key, image_bytes, content_type)

    try:
        report = await engine_client.compliance_scan(
            image_bytes=image_bytes,
            filename=safe_name,
            content_type=content_type,
            metadata=_engine_metadata(meta, user, token),
            calibration_mm_per_px=meta.calibration_mm_per_px,
        )
    except EngineUnavailable:
        storage.delete(image_key)  # do not keep orphaned uploads
        raise

    inspection = Inspection(
        token=token,
        image_key=image_key,
        image_name=safe_name,
        image_mime=content_type or "image/jpeg",
        image_size=len(image_bytes),
        officer_id=user.id,
        remarks=meta.remarks or "",
    )
    db.add(inspection)
    db.flush()

    apply_compliance_report(db, inspection, report)
    inspection.product = upsert_product(db, report, meta, user.id)
    db.commit()
    db.refresh(inspection)
    return inspection