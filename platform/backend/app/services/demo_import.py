"""Demo import: build an inspection from a stored engine demo report.

Lets the whole platform (UI, dashboards, reports) be exercised while the
CV/OCR engine service is offline or for officer training.
"""
from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequest
from app.core.storage import Storage
from app.models.inspection import Inspection
from app.models.user import User
from app.schemas.inspection import InspectionMeta
from app.services.report_loader import FIELD_GENERIC_NAME, apply_compliance_report, upsert_product


def import_demo_report(
    db: Session,
    user: User,
    storage: Storage,
    source: str,
    demo_dir: Path,
    images_dir: Path,
) -> Inspection:
    if not source.endswith(".json"):
        source = f"{source}.json"
    src_path = (demo_dir / source).resolve()
    if not src_path.is_file() or demo_dir.resolve() not in src_path.parents:
        raise BadRequest(f"demo report not found: {source}")

    with open(src_path, encoding="utf-8") as fh:
        report = json.load(fh)

    token = secrets.token_hex(8)
    inspection = Inspection(
        token=token,
        image_key="",
        image_name=source,
        image_mime="image/jpeg",
        image_size=0,
        engine_scan_id=f"demo:{source}",
        officer_id=user.id,
    )
    db.add(inspection)
    db.flush()

    apply_compliance_report(db, inspection, report)
    meta = InspectionMeta(
        product_name=_declaration_text(report, FIELD_GENERIC_NAME),
        category=None,
    )
    inspection.product = upsert_product(db, report, meta, user.id)

    stem = Path(source).stem
    for prefix in ("",):
        for ext in (".jpg", ".jpeg", ".JPG", ".JPEG"):
            candidate = images_dir / f"{prefix}{stem}{ext}"
            if candidate.is_file():
                data = candidate.read_bytes()
                inspection.image_name = candidate.name
                inspection.image_mime = "image/jpeg"
                inspection.image_size = len(data)
                inspection.image_key = f"inspections/{token}/{candidate.name}"
                storage.save(inspection.image_key, data, "image/jpeg")
                break

    db.commit()
    db.refresh(inspection)
    return inspection


def _declaration_text(report: dict, field_name: str) -> str:
    for d in report.get("declarations") or []:
        if d.get("field_name") == field_name:
            return d.get("value") or ""
    return ""


def _now_utc_str() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")