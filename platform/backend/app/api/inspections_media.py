"""Inspection media endpoints: evidence upload, image & evidence streaming.

Image/evidence GETs accept either the Authorization header or an ``access_token``
query parameter so ``<img>``/``<a>`` tags can render them from the browser.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Header, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.exceptions import BadRequest, NotFound, Unauthorized
from app.core.security import get_user_from_token, require_roles
from app.core.storage import get_storage
from app.database import get_db
from app.models.report_evidence import Evidence
from app.models.user import ROLE_ADMIN, ROLE_OFFICER, ROLE_REVIEWER, User
from app.api.inspections import _load

router = APIRouter(prefix="/inspections", tags=["inspections"])


@router.post("/{token}/evidence", status_code=201)
async def attach_evidence(
    token: str,
    files: list[UploadFile] = File(...),
    user: User = Depends(require_roles(ROLE_OFFICER, ROLE_REVIEWER, ROLE_ADMIN)),
    db: Session = Depends(get_db),
):
    """Attach supporting photographs/evidence to an inspection."""
    inspection = _load(db, token)
    storage = get_storage()
    settings = get_settings()
    limit = settings.max_upload_mb * 1024 * 1024
    added = []
    for f in files:
        data = await f.read()
        if not data:
            continue
        if len(data) > limit:
            raise BadRequest(f"file too large: {f.filename}")
        safe = (f.filename or "evidence.bin").replace("\\", "/").split("/")[-1]
        eid = f"{inspection.token}-{len(inspection.evidence) + len(added) + 1}"
        key = f"inspections/{inspection.token}/evidence/{eid}-{safe}"
        storage.save(key, data, f.content_type or "application/octet-stream")
        ev = Evidence(
            inspection_id=inspection.id,
            storage_key=key,
            filename=safe,
            mime_type=f.content_type or "application/octet-stream",
            size_bytes=len(data),
            uploaded_by=user.id,
            created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        db.add(ev)
        added.append(ev)
    db.commit()
    return {"ok": True, "evidence": [e.to_dict() for e in added]}


def _creds(access_token: str | None, authorization: str | None) -> str | None:
    if access_token:
        return access_token
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:]
    return None


def _authorized_user(db: Session, access_token, authorization):
    token = _creds(access_token, authorization)
    if not token:
        raise Unauthorized("missing bearer token")
    return get_user_from_token(token, db)


@router.get("/{token}/image")
def get_image(
    token: str,
    annotated: bool = Query(False),
    access_token: str | None = Query(None),
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
):
    """Stream the stored product image, optionally annotated with zones."""
    _authorized_user(db, access_token, authorization)
    inspection = _load(db, token)
    if not inspection.image_key:
        raise NotFound("no image stored for this inspection")
    data = get_storage().open(inspection.image_key)
    if annotated:
        from app.services.annotation import annotate_image

        zones = (inspection.compliance_json or {}).get("scan", {}).get("zones", [])
        data = annotate_image(data, zones or [])
        return Response(content=data, media_type="image/jpeg")
    return Response(content=data, media_type=inspection.image_mime or "image/jpeg")


@router.get("/{token}/evidence/{evidence_id}")
def get_evidence(
    token: str,
    evidence_id: int,
    access_token: str | None = Query(None),
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
):
    _authorized_user(db, access_token, authorization)
    inspection = _load(db, token)
    ev = (
        db.query(Evidence)
        .filter(Evidence.id == evidence_id, Evidence.inspection_id == inspection.id)
        .first()
    )
    if ev is None:
        raise NotFound("evidence not found")
    data = get_storage().open(ev.storage_key)
    return Response(content=data, media_type=ev.mime_type or "application/octet-stream")