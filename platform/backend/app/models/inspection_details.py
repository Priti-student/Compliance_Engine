"""Child records of an inspection: declarations, violations, font metrics,
report artifacts and supporting evidence."""
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import JSON_VARIANT


class Declaration(Base):
    __tablename__ = "declarations"

    id: Mapped[int] = mapped_column(primary_key=True)
    inspection_id: Mapped[int] = mapped_column(
        ForeignKey("inspections.id", ondelete="CASCADE"), index=True, nullable=False
    )
    inspection = relationship("Inspection", back_populates="declarations")

    field_name: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    value: Mapped[str | None] = mapped_column(Text)
    raw_text: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    method: Mapped[str | None] = mapped_column(String(32))
    source_zone: Mapped[str | None] = mapped_column(String(48))
    qualifiers: Mapped[list] = mapped_column(JSON_VARIANT, default=list)
    rule_id: Mapped[str | None] = mapped_column(String(24))

    def to_dict(self) -> dict:
        return {
            "field_name": self.field_name,
            "value": self.value,
            "raw_text": self.raw_text,
            "confidence": self.confidence,
            "method": self.method,
            "source_zone": self.source_zone,
            "qualifiers": self.qualifiers,
            "rule_id": self.rule_id,
        }


class Violation(Base):
    __tablename__ = "violations"

    id: Mapped[int] = mapped_column(primary_key=True)
    inspection_id: Mapped[int] = mapped_column(
        ForeignKey("inspections.id", ondelete="CASCADE"), index=True, nullable=False
    )
    inspection = relationship("Inspection", back_populates="violations")

    rule_id: Mapped[str] = mapped_column(String(24), index=True, nullable=False)
    rule_reference: Mapped[str | None] = mapped_column(String(128))
    field_name: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(24), default="non_compliant")
    severity: Mapped[str] = mapped_column(String(16), default="medium")
    reason: Mapped[str] = mapped_column(Text, default="")
    evidence: Mapped[dict] = mapped_column(JSON_VARIANT, default=dict)

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "rule_reference": self.rule_reference,
            "field_name": self.field_name,
            "status": self.status,
            "severity": self.severity,
            "reason": self.reason,
            "evidence": self.evidence,
        }