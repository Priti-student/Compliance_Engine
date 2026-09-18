"""User-management schemas (admin)."""
from pydantic import BaseModel, EmailStr, Field

from app.models.user import ROLES


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: EmailStr | None = None
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="officer", pattern="|".join(ROLES))


class UserUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    role: str | None = Field(default=None, pattern="|".join(ROLES))
    is_active: bool | None = None


class ResetPassword(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)


class UserPage(BaseModel):
    total: int
    page: int
    size: int
    items: list[dict]