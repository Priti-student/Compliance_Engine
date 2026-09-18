"""Auth/session schemas."""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserOut(BaseModel):
    id: int
    username: str
    email: str | None = None
    full_name: str
    role: str
    is_active: bool = True
    last_login_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LoginForm(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)