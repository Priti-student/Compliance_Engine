"""Shared helpers for persisting an engine ComplianceReport dict."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.inspection import Inspection
from app.models.inspection_details import Declaration, Violation
from app.models.product import Product
from app.models.report_evidence import FontMetric
from app.schemas.inspection import InspectionMeta

FIELD_GENERIC_NAME = "generic_name_of_commodity"
FIELD_NET_QTY = "net_quantity"
FIELD_MRP = "mrp"
FIELD_MANUFACTURER = "manufacturer_packer_importer"
FIELD_BATCH = "batch_number"


def find_decl(report: dict, field_name: str) -> dict | None:
    for d in report.get("declarations") or []:
        if d.get("field_name") == field_name:
            return d
    return None


def declaration_text(report: dict, field_name: str) -> str:
    d = find_decl(report, field_name)
    return (d or {}).get("value") or ""


def upsert_product(
    db: Session, report: dict, meta: InspectionMeta, created_by: int
) -> Product | None:
    """Create-or-update a product master row from extracted declarations."""
    name = (meta.product_name or declaration_text(report, FIELD_GENERIC_NAME) or "").strip()
    if not name:
        return None
    product = (
        db.query(Product)
        .filter(Product.generic_name.ilike(name))
        .order_by(Product.id.desc())
        .first()
    )
    if product is None:
        product = Product(generic_name=name[:255], created_by=created_by)
        db.add(product)
    product.brand = meta.brand or product.brand
    product.category = meta.category or product.category
    product.net_quantity_text = (
        declaration_text(report, FIELD_NET_QTY) or product.net_quantity_text
    )
    product.mrp = declaration_text(report, FIELD_MRP) or product.mrp
    product.manufacturer = (
        declaration_text(report, FIELD_MANUFACTURER) or product.manufacturer
    )
    product.batch_no = declaration_text(report, FIELD_BATCH) or product.batch_no
    db.flush()
    return product


def apply_compliance_report(db: Session, inspection: Inspection, report: dict) -> None:
    """Write a ComplianceReport JSON dict into ORM rows attached to inspection."""
    inspection.compliance_json = report
    inspection.compliance_status = report.get("compliance_status") or "needs_review"
    inspection.stats_json = report.get("stats") or {}
    inspection.advice_json = report.get("advice") or []

    for d in report.get("declarations") or []:
        db.add(
            Declaration(
                inspection_id=inspection.id,
                field_name=(d.get("field_name") or "")[:64],
                value=d.get("value"),
                raw_text=d.get("raw_text"),
                confidence=float(d.get("confidence") or 0.0),
                method=d.get("method"),
                source_zone=d.get("source_zone"),
                qualifiers=d.get("qualifiers") or [],
                rule_id=d.get("rule_id"),
            )
        )
    for v in report.get("violations") or []:
        db.add(
            Violation(
                inspection_id=inspection.id,
                rule_id=(v.get("rule_id") or "?")[:24],
                rule_reference=(v.get("rule_reference") or "")[:128],
                field_name=(v.get("field_name") or "")[:64],
                status=v.get("status") or "non_compliant",
                severity=v.get("severity") or "medium",
                reason=v.get("reason") or "",
                evidence=v.get("evidence") or {},
            )
        )
    for m in report.get("font_metrics") or []:
        db.add(
            FontMetric(
                inspection_id=inspection.id,
                zone_type=(m.get("zone_type") or "")[:48],
                char_height_px_median=float(m.get("char_height_px_median") or 0.0),
                char_height_mm_median=float(m.get("char_height_mm_median") or 0.0),
                contrast_ratio=float(m.get("contrast_ratio") or 0.0),
                calibrated=bool(m.get("calibrated") or False),
            )
        )