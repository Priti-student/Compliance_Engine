"""User management (admin only) with role-based access control."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequest, NotFound
from app.core.security import CurrentUser, hash_password, require_roles
from app.database import get_db
from app.models.user import ROLE_ADMIN, User
from app.schemas.user import ResetPassword, UserCreate, UserPage, UserUpdate

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_roles(ROLE_ADMIN))])


@router.get("", response_model=UserPage)
def list_users(
    q: str = "",
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(User.username.ilike(like), User.full_name.ilike(like), User.email.ilike(like))
        )
    total = query.count()
    rows = (
        query.order_by(User.id)
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return UserPage(total=total, page=page, size=size, items=[u.public() for u in rows])


@router.post("", status_code=201)
def create_user(
    payload: UserCreate,
    _: CurrentUser,
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.username == payload.username).first():
        raise BadRequest("username already taken")
    if payload.email and db.query(User).filter(User.email == payload.email).first():
        raise BadRequest("email already registered")
    user = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.public()


@router.patch("/{user_id}")
def update_user(
    user_id: int,
    payload: UserUpdate,
    admin: CurrentUser,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise NotFound("user not found")
    if user.id == admin.id and payload.is_active is False:
        raise BadRequest("cannot deactivate your own account")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user.public()


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    admin: CurrentUser,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise NotFound("user not found")
    if user.id == admin.id:
        raise BadRequest("cannot delete your own account")
    user.is_active = False
    db.commit()
    return None


@router.post("/{user_id}/reset-password")
def reset_password(
    user_id: int,
    payload: ResetPassword,
    _: CurrentUser,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise NotFound("user not found")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"ok": True}