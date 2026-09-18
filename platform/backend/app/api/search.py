"""Product-repository search endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.database import get_db
from app.models.user import ROLE_ADMIN, ROLE_OFFICER, ROLE_REVIEWER, User
from app.services import search_service

router = APIRouter(prefix="/search", tags=["search"])

_AUTH = Depends(require_roles(ROLE_OFFICER, ROLE_REVIEWER, ROLE_ADMIN))


@router.get("")
def search_repository(
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
    total, items = search_service.search_inspections(
        db, q=q, status=status, category=category, officer=officer,
        from_date=from_date, to_date=to_date, page=page, size=size,
    )
    return {"total": total, "page": page, "size": size, "items": items}


@router.get("/suggest")
def suggest(
    q: str = "",
    limit: int = Query(10, ge=1, le=25),
    db: Session = Depends(get_db),
    _: User = _AUTH,
):
    return {"suggestions": search_service.suggest(db, q=q, limit=limit)}