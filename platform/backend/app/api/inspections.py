"""Inspection endpoints: demo import, scan upload, list, detail, review."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.exceptions import BadRequest, NotFound
from app.core.security import require_roles
from app.core.storage import get_storage
from app.database import get_db
from app.models.inspection import Inspection
from app.models.user import ROLE_ADMIN, ROLE_OFFICER, ROLE_REVIEWER, User
from app.schemas.inspection import DemoImport, InspectionMeta, InspectionPage, InspectionUpdate
from app.services import inspection_service as inspect_svc
from app.services import report_service
from app.services.demo_import import import_demo_report

router = APIRouter(prefix="/inspections", tags=["inspections"])

_AUTH = Depends(require_roles(ROLE_OFFICER, ROLE_REVIEWER, ROLE_ADMIN))


def _detail(inspection: Inspection) -> dict:
    return {
        "id": inspection.id,
        "token": inspection.token,
        "product": inspection.product.summary() if inspection.product else None,
        "compliance_status": inspection.compliance_status,
        "workflow_status": inspection.workflow_status,
        "stats": inspection.stats_json,
        "advice": inspection.advice_json,
        "remarks": inspection.remarks,
        "image_name": inspection.image_name,
        "engine_scan_id": inspection.engine_scan_id,
        "officer": inspection.officer.public() if inspection.officer else None,
        "reviewer": inspection.reviewer.public() if inspection.reviewer else None,
        "reviewed_at": inspection.reviewed_at,
        "declarations": [d.to_dict() for d in inspection.declarations],
        "violations": [v.to_dict() for v in inspection.violations],
        "font_metrics": [m.to_dict() for m in inspection.font_metrics],
        "evidence": [e.to_dict() for e in inspection.evidence],
        "reports": [r.to_dict() for r in inspection.reports],
        "compliance_json": inspection.compliance_json,
        "created_at": inspection.created_at.isoformat() if inspection.created_at else None,
        "updated_at": inspection.updated_at.isoformat() if inspection.updated_at else None,
    }


def _load(db: Session, token: str) -> Inspection:
    inspection = db.query(Inspection).filter(Inspection.token == token).first()
    if inspection is None:
        raise NotFound(f"inspection not found: {token}")
    return inspection


@router.post("/from-demo", status_code=201)
def import_demo(
    payload: DemoImport,
    user: User = _AUTH,
    db: Session = Depends(get_db),
):
    """Import a stored engine demo report (training / offline mode)."""
    settings = get_settings()
    inspection = import_demo_report(
        db,
        user,
        get_storage(),
        payload.source,
        settings.demo_import_dir_abs,
        settings.demo_engine_root,
    )
    report_service.generate_all(db, inspection, user, get_storage())
    return {"ok": True, "token": inspection.token}


@router.post("", status_code=201)
async def create_inspection(
    file: UploadFile = File(...),
    metadata: str = Form("{}"),
    current_user: User = _AUTH,
    db: Session = Depends(get_db),
):
    """Upload one package image; engine scans it; everything is persisted."""
    settings = get_settings()
    content_type = (file.content_type or "").lower()
    if not content_type.startswith("image/"):
        raise BadRequest("upload must be an image (content-type image/*)")

    data = await file.read()
    limit = settings.max_upload_mb * 1024 * 1024
    if not data:
        raise BadRequest("empty upload")
    if len(data) > limit:
        raise BadRequest(f"image too large (max {settings.max_upload_mb} MB)")

    try:
        meta_dict = json.loads(metadata or "{}")
    except json.JSONDecodeError as exc:
        raise BadRequest("metadata must be a valid JSON object") from exc
    meta = InspectionMeta(**{k: v for k, v in meta_dict.items() if k in InspectionMeta.model_fields})

    inspection = await inspect_svc.create_inspection(
        db, current_user, get_storage(),
        image_bytes=data,
        filename=file.filename or "upload.jpg",
        content_type=content_type,
        meta=meta,
    )

    # generate PDF + XLSX + JSON artifacts (best-effort)
    try:
        report_service.generate_all(db, inspection, current_user, get_storage())
    except Exception:
        db.rollback()

    db.refresh(inspection)
    return _detail(inspection)


@router.get("", response_model=InspectionPage)
def list_inspections(
    q: str = "",
    status: str | None = Query(None, alias="compliance_status"),
    category: str | None = None,
    officer: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = _AUTH,
):
    from app.services.search_service import search_inspections

    total, items = search_inspections(
        db, q=q, status=status, category=category, officer=officer,
        from_date=from_date, to_date=to_date, page=page, size=size,
    )
    return InspectionPage(total=total, page=page, size=size, items=items)


@router.get("/{token}")
def get_inspection(
    token: str,
    db: Session = Depends(get_db),
    _: User = _AUTH,
):
    return _detail(_load(db, token))


@router.patch("/{token}")
def update_inspection(
    token: str,
    payload: InspectionUpdate,
    reviewer: User = Depends(require_roles(ROLE_REVIEWER, ROLE_ADMIN)),
    db: Session = Depends(get_db),
):
    """Mark reviewed/approved and add remarks (Reviewer/Admin)."""
    inspection = _load(db, token)
    if payload.workflow_status:
        inspection.workflow_status = payload.workflow_status
        inspection.reviewed_by = reviewer.id
        from app.services.inspection_service import _now_utc_str

        inspection.reviewed_at = _now_utc_str()
    if payload.remarks is not None:
        inspection.remarks = payload.remarks
    db.commit()
    db.refresh(inspection)
    return _detail(inspection)