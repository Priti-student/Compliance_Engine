"""Font metrics, report artifacts and evidence attachment models."""
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FontMetric(Base):
    __tablename__ = "font_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    inspection_id: Mapped[int] = mapped_column(
        ForeignKey("inspections.id", ondelete="CASCADE"), index=True, nullable=False
    )
    inspection = relationship("Inspection", back_populates="font_metrics")

    zone_type: Mapped[str] = mapped_column(String(48), nullable=False)
    char_height_px_median: Mapped[float] = mapped_column(Float, default=0.0)
    char_height_mm_median: Mapped[float] = mapped_column(Float, default=0.0)
    contrast_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    calibrated: Mapped[bool] = mapped_column(Boolean, default=False)

    def to_dict(self) -> dict:
        return {
            "zone_type": self.zone_type,
            "char_height_px_median": self.char_height_px_median,
            "char_height_mm_median": self.char_height_mm_median,
            "contrast_ratio": self.contrast_ratio,
            "calibrated": self.calibrated,
        }


class ReportArtifact(Base):
    __tablename__ = "report_artifacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    inspection_id: Mapped[int] = mapped_column(
        ForeignKey("inspections.id", ondelete="CASCADE"), index=True, nullable=False
    )
    inspection = relationship("Inspection", back_populates="reports")

    report_type: Mapped[str] = mapped_column(String(8), nullable=False)  # pdf|xlsx|json
    storage_key: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[str] = mapped_column(String(32), default="")

    def to_dict(self) -> dict:
        return {
            "report_type": self.report_type,
            "filename": self.filename,
            "size_bytes": self.size_bytes,
            "created_by": self.created_by,
            "created_at": self.created_at,
        }


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    inspection_id: Mapped[int] = mapped_column(
        ForeignKey("inspections.id", ondelete="CASCADE"), index=True, nullable=False
    )
    inspection = relationship("Inspection", back_populates="evidence")

    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(64), default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[str] = mapped_column(String(32), default="")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "uploaded_by": self.uploaded_by,
            "created_at": self.created_at,
        }