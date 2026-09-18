"""Product-repository search over inspections & products."""
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, cast, or_
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequest
from app.models.inspection import Inspection
from app.models.product import Product
from app.models.user import User


def search_inspections(
    db: Session,
    q: str = "",
    status: str | None = None,
    category: str | None = None,
    officer: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[int, list[dict]]:
    """Search the repository of scanned products/inspections.

    Free-text ``q`` matches product name/brand/manufacturer/image/remarks.
    Additional filters narrow by compliance status, category, officer and
    created-date range. Returns (total, items).
    """
    query = db.query(Inspection).join(
        Product, Inspection.product_id == Product.id, isouter=True
    )

    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Product.generic_name.ilike(like),
                Product.brand.ilike(like),
                Product.manufacturer.ilike(like),
                Inspection.image_name.ilike(like),
                Inspection.remarks.ilike(like),
                Inspection.token.ilike(like),
            )
        )
    if status:
        query = query.filter(Inspection.compliance_status == status)
    if category:
        query = query.filter(Product.category == category)
    if officer:
        like = f"%{officer.strip()}%"
        query = query.join(User, Inspection.officer_id == User.id)
        query = query.filter(or_(User.username.ilike(like), User.full_name.ilike(like)))
    if from_date:
        try:
            from_d = date.fromisoformat(from_date)
        except ValueError as exc:
            raise BadRequest("from_date must be YYYY-MM-DD") from exc
        query = query.filter(cast(Inspection.created_at, Date) >= cast(from_d, Date))
    if to_date:
        try:
            to_d = date.fromisoformat(to_date)
        except ValueError as exc:
            raise BadRequest("to_date must be YYYY-MM-DD") from exc
        query = query.filter(cast(Inspection.created_at, Date) <= cast(to_d, Date))

    total = query.count()
    rows = (
        query.order_by(Inspection.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return total, [r.summary() for r in rows]


def suggest(db: Session, q: str = "", limit: int = 10) -> list[str]:
    if not q.strip():
        return []
    like = f"%{q.strip()}%"
    rows = (
        db.query(Product.generic_name)
        .filter(Product.generic_name.ilike(like))
        .distinct()
        .order_by(Product.generic_name)
        .limit(limit)
        .all()
    )
    return [r[0] for r in rows]