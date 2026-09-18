"""Product repository endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequest, NotFound
from app.core.security import require_roles
from app.database import get_db
from app.models.product import Product
from app.models.user import ROLE_ADMIN, ROLE_OFFICER, ROLE_REVIEWER, User
from app.schemas.product import ProductCreate, ProductPage, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])

_AUTH = Depends(require_roles(ROLE_OFFICER, ROLE_REVIEWER, ROLE_ADMIN))
_REVIEWER = Depends(require_roles(ROLE_REVIEWER, ROLE_ADMIN))


@router.get("", response_model=ProductPage)
def list_products(
    q: str = "",
    category: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = _AUTH,
):
    query = db.query(Product)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Product.generic_name.ilike(like),
                Product.brand.ilike(like),
                Product.manufacturer.ilike(like),
            )
        )
    if category:
        query = query.filter(Product.category == category)
    total = query.count()
    rows = (
        query.order_by(Product.generic_name)
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return ProductPage(total=total, page=page, size=size, items=[p.summary() for p in rows])


@router.post("", status_code=201)
def create_product(
    payload: ProductCreate,
    current_user: User = _AUTH,
    db: Session = Depends(get_db),
):
    if db.query(Product).filter(Product.generic_name == payload.generic_name).first():
        raise BadRequest("product with this name already exists")
    product = Product(**payload.model_dump(), created_by=current_user.id)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product.summary()


@router.get("/{product_id}")
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = _AUTH,
):
    product = db.get(Product, product_id)
    if product is None:
        raise NotFound("product not found")
    data = product.summary()
    data["inspections"] = [i.summary() for i in product.inspections]
    return data


@router.patch("/{product_id}")
def update_product(
    product_id: int,
    payload: ProductUpdate,
    _: User = _REVIEWER,
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)
    if product is None:
        raise NotFound("product not found")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product.summary()


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    _: User = Depends(require_roles(ROLE_ADMIN)),
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)
    if product is None:
        raise NotFound("product not found")
    if product.inspections:
        raise BadRequest("cannot delete a product that has inspections")
    db.delete(product)
    db.commit()
    return None