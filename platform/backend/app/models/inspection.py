"""Inspection (scan) model."""
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import JSON_VARIANT, TimestampMixin

# workflow statuses
WF_OPEN = "open"
WF_REVIEWED = "reviewed"
WF_APPROVED = "approved"
WORKFLOW_STATUSES = (WF_OPEN, WF_REVIEWED, WF_APPROVED)

COMPLIANCE_STATUSES = ("compliant", "non_compliant", "needs_review", "not_applicable")


class Inspection(Base, TimestampMixin):
    __tablename__ = "inspections"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)

    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), index=True)
    product = relationship("Product", back_populates="inspections")

    # source image
    image_key: Mapped[str] = mapped_column(String(512), nullable=False)
    image_name: Mapped[str] = mapped_column(String(255), nullable=False)
    image_mime: Mapped[str] = mapped_column(String(64), default="image/jpeg")
    image_size: Mapped[int] = mapped_column(Integer, default=0)

    # engine provenance
    engine_scan_id: Mapped[str | None] = mapped_column(String(64))

    # compliance summary
    compliance_status: Mapped[str] = mapped_column(
        String(24), index=True, default="needs_review", nullable=False
    )
    workflow_status: Mapped[str] = mapped_column(
        String(16), default=WF_OPEN, index=True, nullable=False
    )
    compliance_json: Mapped[dict] = mapped_column(JSON_VARIANT, default=dict, nullable=False)
    stats_json: Mapped[dict] = mapped_column(JSON_VARIANT, default=dict, nullable=False)
    advice_json: Mapped[list] = mapped_column(JSON_VARIANT, default=list, nullable=False)
    remarks: Mapped[str] = mapped_column(Text, default="")

    officer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    officer = relationship("User", foreign_keys=[officer_id])
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    reviewed_at: Mapped[str | None] = mapped_column(String(32))

    declarations = relationship(
        "Declaration", back_populates="inspection", cascade="all, delete-orphan"
    )
    violations = relationship(
        "Violation", back_populates="inspection", cascade="all, delete-orphan"
    )
    font_metrics = relationship(
        "FontMetric", back_populates="inspection", cascade="all, delete-orphan"
    )
    reports = relationship(
        "ReportArtifact", back_populates="inspection", cascade="all, delete-orphan"
    )
    evidence = relationship(
        "Evidence", back_populates="inspection", cascade="all, delete-orphan"
    )

    def summary(self) -> dict:
        return {
            "id": self.id,
            "token": self.token,
            "product": self.product.summary() if self.product else None,
            "compliance_status": self.compliance_status,
            "workflow_status": self.workflow_status,
            "stats": self.stats_json,
            "officer": self.officer.public() if self.officer else None,
            "reviewed_by": self.reviewer.public() if self.reviewer else None,
            "reviewed_at": self.reviewed_at,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }