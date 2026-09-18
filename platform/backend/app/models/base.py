"""Common column types/mixins for ORM models.

JSON is used with a PostgreSQL JSONB variant so the models work unchanged on
SQLite (used by the test-suite) while production gets native JSONB.
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, JSON as SA_JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

Guid = None  # placeholder kept out of the way

JSON_VARIANT = SA_JSON().with_variant(JSONB(), "postgresql")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )