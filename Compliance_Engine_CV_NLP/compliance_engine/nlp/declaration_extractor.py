"""
Phase 6 - Declaration extraction (NLP).

Takes the Phase 1-4 ScanResult (zones + full-image OCR) and produces
structured DeclarationInfo rows for each mandatory declaration that the
rule engine (Phase 7) validates against rules/lmpc_rules_database.json.

Strategy (deterministic first, ML later):
  1. regex pass - EXTRACTORS in regex_patterns.py, run per zone.
  2. heuristic fallback - zone keyword text may not match a strict pattern
     but the zone was already tagged (e.g. a consumer-care block with no
     phone/email yet, a manufacturer block whose address got merged away).
     In that case the field is recorded with an empty value so the rule
     engine can distinguish "missing value" from "extraction failure".
  3. (Planned upgrade) spaCy EntityRuler + fine-tuned BERT residue classifier
     to resolve ambiguous multi-line blocks and OCR noise; the extractor's
     return schema is already the handoff contract for that layer.
"""
from typing import List

from compliance_engine.nlp import regex_patterns as rx
from compliance_engine.schema import DeclarationInfo, ScanResult

# Concrete single-value fields extracted by the regex engine.
_STRICT_FIELDS = {
    "generic_name_of_commodity": {"rule_id": "MD-02"},
    "unit_sale_price": {"rule_id": "MD-10"},
    "mrp": {"rule_id": "MD-05"},
    "net_quantity": {"rule_id": "MD-03"},
    "month_year_of_manufacture": {"rule_id": "MD-04"},
    "use_by_date": {"rule_id": "MD-07"},   # consumer-care-ish but separate
    "fssai_license": {"rule_id": "FSSAI-01"},
    "batch_number": {"rule_id": "BATCH-01"},
    "consumer_phone": {"rule_id": "MD-07"},
    "consumer_email": {"rule_id": "MD-07"},
}

# Fields where a zone might exist but the regex found no value -
# these become DeclarationInfo with empty value + source zone set, so the
# rule engine can flag "missing value" rather than "not detected".
_OPTIONAL_EMPTY_FIELDS = {"consumer_care_details", "manufacturer_packer_importer"}


def extract_declarations(scan: ScanResult) -> List[DeclarationInfo]:
    """Run Phase 6 over a Phase 1-4 ScanResult and return declaration rows."""
    declarations: List[DeclarationInfo] = []

    # Normalize zone text: OCR often returns newline-per-token; merge lines so
    # patterns like "MRP\n20.00" still match "MRP 20.00".
    zone_texts: List[tuple] = []   # (zone_type, text)
    for zone in scan.zones or []:
        text = _collapse(zone.text)
        zone_texts.append((zone.zone_type, text))

    full_text = _collapse((scan.full_image_ocr.text if scan.full_image_ocr else ""))

    # Pass 1: strict regex extraction per zone.
    for field_name, fn in rx.EXTRACTORS:
        if field_name == "generic_name_of_commodity":
            # Product/generic name is inferred from the whole-image OCR only
            # (a brand inside an address block or a 'Month' token in a date
            # block is not the generic commodity name).
            continue
        for zone_type, text in zone_texts:
            for hit in fn(text):
                declarations.append(DeclarationInfo(
                    field_name=field_name,
                    value=hit.get("value", ""),
                    raw_text=text[:_slice_width()],
                    confidence=0.85 if hit.get("value") else 0.4,
                    method="regex",
                    source_zone=zone_type,
                    # qualifiers are extracted from a TIGHT window around the
                    # matched value (in the extractor), not the whole zone text,
                    # so unrelated text (e.g. a nutrition-table 'Approx.') can't
                    # mis-flag a net-quantity declaration.
                    qualifiers=hit.get("qualifiers", []),
                    rule_id=_STRICT_FIELDS.get(field_name, {}).get("rule_id", ""),
                ))

    # Pass 2: optical zone presence as evidence even when regex found nothing
    # (e.g. manufacturer/consumer-care blocks that OCR'd with no phone/email).
    present_zones = {zt for zt, _ in zone_texts}
    for zone_type in rx.ZONE_TO_FIELD:
        if zone_type not in present_zones:
            continue
        field_name = rx.ZONE_TO_FIELD[zone_type]
        if field_name not in _OPTIONAL_EMPTY_FIELDS:
            continue
        if any(d.field_name == field_name for d in declarations):
            continue
        # For the manufacturer block use the WHOLE image OCR text as context:
        # OCR often splits/merges the address lines, so the street/PIN evidence
        # for the NER check may live anywhere on the label, not inside the
        # zone bbox.
        raw = full_text[:_slice_width()] if field_name == "manufacturer_packer_importer" \
            else text[:_slice_width()]
        declarations.append(DeclarationInfo(
            field_name=field_name,
            value="",
            raw_text=raw,
            confidence=0.3,
            method="heuristic",
            source_zone=zone_type,
            rule_id="",
        ))

    # Pass 3: full-image scan profit (catch declarations the zone detector
    # missed but that appear somewhere in the whole-image OCR text).
    for field_name, fn in rx.EXTRACTORS:
        for hit in fn(full_text):
            if any(d.field_name == field_name and d.value == hit.get("value")
                   for d in declarations):
                continue
            declarations.append(DeclarationInfo(
                field_name=field_name,
                value=hit.get("value", ""),
                raw_text=full_text[:_slice_width()],
                confidence=0.6,
                method="regex",
                source_zone="full_image",
                rule_id=_STRICT_FIELDS.get(field_name, {}).get("rule_id", ""),
            ))

    return declarations


def _collapse(text: str) -> str:
    """Merge OCR line breaks into spaces (e.g. 'MFD:\n10/07/2024')."""
    return " ".join(text.split())


def _slice_width() -> int:
    return 4000