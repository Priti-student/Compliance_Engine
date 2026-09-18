"""Inspection and report schemas."""
from pydantic import BaseModel, Field


class InspectionMeta(BaseModel):
    """Free-form metadata submitted with an image upload to /inspections."""

    product_name: str | None = None
    brand: str | None = None
    category: str | None = None
    manufacturer: str | None = None
    remarks: str | None = None
    calibration_mm_per_px: float = 0.0
    enforce_unit_sale_price: bool = False
    package_flagged_as_imported: bool = False


class InspectionUpdate(BaseModel):
    workflow_status: str | None = Field(default=None, pattern="open|reviewed|approved")
    remarks: str | None = None


class InspectionPage(BaseModel):
    total: int
    page: int
    size: int
    items: list[dict]


class ReportGenerate(BaseModel):
    report_type: str = Field(default="pdf", pattern="pdf|xlsx|json")


class DemoImport(BaseModel):
    """Import a stored demo compliance report (engine offline / training mode)."""

    source: str = Field(description="filename inside DEMO_IMPORT_DIR, e.g. package_001.json")