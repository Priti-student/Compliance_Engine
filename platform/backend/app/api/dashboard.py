"""Dashboard endpoints for enforcement monitoring."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.database import get_db
from app.models.user import ROLE_ADMIN, ROLE_OFFICER, ROLE_REVIEWER, User
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_AUTH = Depends(require_roles(ROLE_OFFICER, ROLE_REVIEWER, ROLE_ADMIN))


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db), _: User = _AUTH):
    return dashboard_service.summary(db)


@router.get("/status-distribution")
def status_distribution(db: Session = Depends(get_db), _: User = _AUTH):
    return dashboard_service.status_distribution(db)


@router.get("/violation-trend")
def violation_trend(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    _: User = _AUTH,
):
    return dashboard_service.violation_trend(db, days=days)


@router.get("/top-violations")
def top_violations(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    _: User = _AUTH,
):
    return dashboard_service.top_violations(db, limit=limit)


@router.get("/officer-activity")
def officer_activity(db: Session = Depends(get_db), _: User = _AUTH):
    return dashboard_service.officer_activity(db)


@router.get("/category-stats")
def category_stats(db: Session = Depends(get_db), _: User = _AUTH):
    return dashboard_service.category_stats(db)


@router.get("/recent")
def recent(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    _: User = _AUTH,
):
    return dashboard_service.recent(db, limit=limit)