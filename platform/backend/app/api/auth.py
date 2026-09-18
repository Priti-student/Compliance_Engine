"""Auth endpoints: login (OAuth2 password flow), me, refresh."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_current_user, verify_password
from app.database import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == form.username).first()
    if user is None or not verify_password(form.password, user.password_hash):
        from app.core.exceptions import Unauthorized

        raise Unauthorized("Incorrect username or password")
    if not user.is_active:
        from app.core.exceptions import Forbidden

        raise Forbidden("User account is disabled")
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    token = create_access_token(user)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(current_user: User = Depends(get_current_user)):
    return TokenResponse(access_token=create_access_token(current_user), user=UserOut.model_validate(current_user))