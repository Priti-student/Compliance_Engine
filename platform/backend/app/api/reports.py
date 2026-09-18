"""Report endpoints: list / generate / download artifacts."""
from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.exceptions import NotFound, Unauthorized
from app.core.security import get_user_from_token, require_roles
from app.core.storage import get_storage
from app.database import get_db
from app.models.user import ROLE_ADMIN, ROLE_OFFICER, ROLE_REVIEWER, User
from app.schemas.inspection import ReportGenerate
from app.services import report_service
from app.api.inspections import _load

router = APIRouter(prefix="/reports", tags=["reports"])

_AUTH = Depends(require_roles(ROLE_OFFICER, ROLE_REVIEWER, ROLE_ADMIN))

_MIME = {
    "pdf": "application/pdf",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "json": "application/json",
}


@router.get("/inspection/{token}")
def list_reports(
    token: str,
    db: Session = Depends(get_db),
    _: User = _AUTH,
):
    inspection = _load(db, token)
    return [r.to_dict() for r in inspection.reports]


@router.post("/{token}")
def generate_report(
    token: str,
    payload: ReportGenerate,
    user: User = _AUTH,
    db: Session = Depends(get_db),
):
    """(Re)generate a PDF / XLSX / JSON artifact for an inspection."""
    inspection = _load(db, token)
    art = report_service.generate_artifact(
        db, inspection, user, get_storage(), payload.report_type
    )
    return {"ok": True, "artifact": art.to_dict()}


@router.get("/{token}/{report_type}")
def download_report(
    token: str,
    report_type: str,
    access_token: str | None = Query(None),
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
):
    if report_type not in _MIME:
        raise NotFound("report type must be pdf, xlsx or json")
    if access_token:
        get_user_from_token(access_token, db)
    elif authorization and authorization.lower().startswith("bearer "):
        get_user_from_token(authorization[7:], db)
    else:
        raise Unauthorized("missing bearer token")

    inspection = _load(db, token)
    art = report_service.get_artifact_or_404(db, inspection, report_type)
    data = get_storage().open(art.storage_key)
    headers = {
        "Content-Disposition": f'attachment; filename="{art.filename}"',
        "Cache-Control": "no-store",
    }
    return Response(content=data, media_type=_MIME[report_type], headers=headers)