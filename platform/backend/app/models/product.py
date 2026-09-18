"""Product repository model."""
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    generic_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    brand: Mapped[str | None] = mapped_column(String(255))
    category: Mapped[str | None] = mapped_column(String(64), index=True)
    manufacturer: Mapped[str | None] = mapped_column(Text)
    packer: Mapped[str | None] = mapped_column(Text)
    importer: Mapped[str | None] = mapped_column(Text)
    net_quantity_text: Mapped[str | None] = mapped_column(String(64))
    mrp: Mapped[str | None] = mapped_column(String(32))
    batch_no: Mapped[str | None] = mapped_column(String(64))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    inspections = relationship("Inspection", back_populates="product")

    def summary(self) -> dict:
        return {
            "id": self.id,
            "generic_name": self.generic_name,
            "brand": self.brand,
            "category": self.category,
            "manufacturer": self.manufacturer,
            "packer": self.packer,
            "importer": self.importer,
            "net_quantity_text": self.net_quantity_text,
            "mrp": self.mrp,
            "batch_no": self.batch_no,
        }