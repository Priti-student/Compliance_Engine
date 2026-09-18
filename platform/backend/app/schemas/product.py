"""Product schemas."""
from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    generic_name: str = Field(min_length=1, max_length=255)
    brand: str | None = None
    category: str | None = None
    manufacturer: str | None = None
    packer: str | None = None
    importer: str | None = None
    net_quantity_text: str | None = None
    mrp: str | None = None
    batch_no: str | None = None


class ProductUpdate(BaseModel):
    generic_name: str | None = Field(default=None, min_length=1, max_length=255)
    brand: str | None = None
    category: str | None = None
    manufacturer: str | None = None
    packer: str | None = None
    importer: str | None = None
    net_quantity_text: str | None = None
    mrp: str | None = None
    batch_no: str | None = None


class ProductPage(BaseModel):
    total: int
    page: int
    size: int
    items: list[dict]