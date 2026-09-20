"""
Phase 7 - Validator primitives.

Implements each `validation_logic.type` referenced in rules/lmpc_rules_database.json
in a data-driven way so the rule engine's evaluate() just looks at
rule.validation_logic and dispatches. New rule types can be added by writing a
function here (and editing the JSON), with no changes to the rule engine.

Each validator signature: validator(declaration, rule, ctx) -> Violation
where ctx carries extra context (calibration, font metrics, product metadata)
used by cross-checking rules.
"""
import re
from typing import Optional

from compliance_engine import config
from compliance_engine.schema import Violation

_SEVERITY_MISSING = "high"
_SEVERITY_FORMAT = "medium"
_SEVERITY_FONT = "medium"


def _base_reason(rule, declaration) -> str:
    if declaration is None:
        return f"Missing mandatory declaration: {rule.field_name}"
    if not declaration.value:
        return (f"Declaration '{rule.field_name}' detected but no value "
                f"extracted from zone '{declaration.source_zone}'")
    return f"Declaration '{rule.field_name}' did not validate"


def presence_check(declaration, rule, ctx) -> Optional[Violation]:
    """Presence only: compliant when a non-empty value was extracted."""
    if declaration is not None and declaration.value:
        return None
    return Violation(
        rule_id=rule.rule_id, rule_reference=rule.rule_reference,
        field_name=rule.field_name, status="missing", severity=_SEVERITY_MISSING,
        reason=_base_reason(rule, declaration),
        evidence={"source_zone": declaration.source_zone if declaration else "",
                  "raw_text": declaration.raw_text if declaration else ""},
    )


_ALLOWED_UNITS = {"g", "kg", "ml", "l", "cm", "m", "sq cm", "sq m", "number", "N", "U"}
_BAD_UNITS = {"dozen", "score", "gross", "piece", "drums"}


def presence_and_unit_check(declaration, rule, ctx) -> Optional[Violation]:
    """Net quantity: present + allowed SI unit + no qualifying words.

    Qualifying-word detection uses the extractor's tight-window qualifiers
    (declaration.qualifiers) and the extracted value only — NOT the whole zone
    / full-image OCR text. This prevents a nutrition-table 'Approx. per 100g'
    elsewhere on the label from mis-flagging a clean 'Net Qty 52 g' line.
    """
    fail = presence_check(declaration, rule, ctx)
    if fail is not None:
        return fail

    qualifiers = list(declaration.qualifiers or [])
    value_text = declaration.value.lower()
    qualifiers += [q for q in
                   ("about", "approx", "approximately", "minimum",
                    "not less than", "more than")
                   if q in value_text]
    if qualifiers:
        return Violation(
            rule_id=rule.rule_id, rule_reference=rule.rule_reference,
            field_name=rule.field_name, status="non_compliant",
            severity=_SEVERITY_FORMAT,
            reason=f"Net quantity uses qualifying/misleading words: {sorted(set(qualifiers))}",
            evidence={"value": declaration.value},
        )
    bad_unit = next((b for b in _BAD_UNITS if b in value_text), None)
    if bad_unit:
        return Violation(
            rule_id=rule.rule_id, rule_reference=rule.rule_reference,
            field_name=rule.field_name, status="non_compliant",
            severity=_SEVERITY_FORMAT,
            reason=f"Net quantity uses non-standard unit '{bad_unit}' (Rule 13(4))",
            evidence={"value": declaration.value},
        )
    return None


_INDIAN_DATE_RE = re.compile(r"\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b")
_MONTH_YEAR_RE = re.compile(
    r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4}\b",
    re.IGNORECASE,
)


def presence_and_date_format_check(declaration, rule, ctx) -> Optional[Violation]:
    """Month/year of manufacture: MM/YYYY or month-name + year."""
    fail = presence_check(declaration, rule, ctx)
    if fail is not None:
        return fail

    value = declaration.value
    if _MONTH_YEAR_RE.search(value) or re.search(r"\b\d{1,2}[/\-]\d{4}\b", value):
        return None
    if _INDIAN_DATE_RE.search(value):
        return None   # full dd/mm/yyyy still acceptable
    return Violation(
        rule_id=rule.rule_id, rule_reference=rule.rule_reference,
        field_name=rule.field_name, status="non_compliant",
        severity=_SEVERITY_FORMAT,
        reason=f"Manufacture date '{value}' is not in MM/YYYY or month-name+YYYY format",
        evidence={"value": value},
    )


_MRP_VALUE_RE = re.compile(r"\d{1,6}(?:\.\d{1,2})?")


_MRP_LABEL_CHECK_RE = re.compile(r"\bm\.?\s?r\.?\s?[pe]\b|maximum\s+retail\s+price", re.IGNORECASE)


def format_regex_and_value_check(declaration, rule, ctx) -> Optional[Violation]:
    """MRP: label present, paise correctly rounded; 'incl. of all taxes'
    qualifier checked but downgraded to needs_review when not OCR-visible
    (a short/garbled OCR window is not proof the qualifier is absent).
    """
    fail = presence_check(declaration, rule, ctx)
    if fail is not None:
        return fail

    text = (declaration.value + " " + declaration.raw_text).lower()
    if not _MRP_LABEL_CHECK_RE.search(text):
        return Violation(
            rule_id=rule.rule_id, rule_reference=rule.rule_reference,
            field_name=rule.field_name, status="non_compliant",
            severity=_SEVERITY_FORMAT,
            reason="MRP label not found",
            evidence={"value": declaration.value},
        )

    # Paise rounding: 0.00 or 0.50 only (Rule 6(1)(e)).
    amt = _MRP_VALUE_RE.search(declaration.value)
    if amt:
        value = float(amt.group(0))
        paise = round((value - int(value)) * 100)
        if not (paise == 0 or paise == 50):
            return Violation(
                rule_id=rule.rule_id, rule_reference=rule.rule_reference,
                field_name=rule.field_name, status="non_compliant",
                severity=_SEVERITY_FORMAT,
                reason=(f"MRP 'Rs. {value:g}' not rounded to nearest 50 paise "
                        f"(0.00 or 0.50 mandatory)"),
                evidence={"value": declaration.value},
            )

    # 'incl. of all taxes' qualifier: OCR may not have captured it even when
    # printed -> review note, not a hard violation or a verdict blocker
    # (see config.MRP_QUALIFIER_OCR_MISS_KIND).
    if "incl" not in text and "inclusive of all taxes" not in text:
        return Violation(
            rule_id=rule.rule_id, rule_reference=rule.rule_reference,
            field_name=rule.field_name, status="needs_review", severity="low",
            reason="MRP 'inclusive of all taxes' qualifier not visible in OCR; "
                   "verify on the physical label",
            evidence={"value": declaration.value,
                      "kind": getattr(config, "MRP_QUALIFIER_OCR_MISS_KIND", "referral")},
        )
    return None


_PHONE_OR_EMAIL_RE = re.compile(r"(?:\d{10,}|[\w.+-]+@[\w-]+\.[\w.]+)")


def presence_and_contact_format_check(declaration, rule, ctx) -> Optional[Violation]:
    """Consumer-care: a detected care block must carry a phone/email contact."""
    if declaration is None:
        return presence_check(declaration, rule, ctx)
    text = f"{declaration.value} {declaration.raw_text}".strip()
    if not text:
        return presence_check(declaration, rule, ctx)
    if not _PHONE_OR_EMAIL_RE.search(text):
        return Violation(
            rule_id=rule.rule_id, rule_reference=rule.rule_reference,
            field_name=rule.field_name, status="non_compliant",
            severity=_SEVERITY_FORMAT,
            reason="Consumer-care block present but no resolvable phone/email",
            evidence={"value": declaration.value, "block_text": text[:200]},
        )
    return None


def presence_and_ner_check(declaration, rule, ctx) -> Optional[Violation]:
    """Manufacturer/packer/importer: a detected block must have address evidence."""
    if declaration is None:
        return presence_check(declaration, rule, ctx)
    text = f"{declaration.value} {declaration.raw_text}".strip()
    if not text:
        return presence_check(declaration, rule, ctx)
    # Address heuristic: street/pincode/Nagar/road/PIN token.
    has_address = bool(re.search(
        r"\b(?:road?|street|st\.?|nagar|puri|village|colony|district|"
        r"pincode|pin\s*[-:]?\s*\d{6}|-?\s*\d{6}\b)",
        text, re.IGNORECASE,
    ))
    if not has_address:
        return Violation(
            rule_id=rule.rule_id, rule_reference=rule.rule_reference,
            field_name=rule.field_name, status="non_compliant",
            severity=_SEVERITY_FORMAT,
            reason="Manufacturer block present but no resolvable address evidence",
            evidence={"block_text": text[:200]},
        )
    return None


def conditional_presence_check(declaration, rule, ctx) -> Optional[Violation]:
    """Dimensions / country-of-origin: only applies when a condition is met."""
    condition = (rule.validation_logic or {}).get("condition", "")
    metadata = getattr(ctx, "metadata", {}) or {}
    if condition and not _condition_met(condition, metadata):
        return Violation(
            rule_id=rule.rule_id, rule_reference=rule.rule_reference,
            field_name=rule.field_name, status="not_applicable", severity="low",
            reason=f"Not applicable (condition '{condition}' not met)",
            evidence={},
        )
    return presence_check(declaration, rule, ctx)


def _condition_met(condition: str, metadata: dict) -> bool:
    """Extremely small safe condition evaluator (== true/false) for the JSON DB."""
    for key, truthy in metadata.items():
        if condition == f"{key} == true" and truthy:
            return True
        if condition == f"{key} == false" and not truthy:
            return True
    return False


def presence_check_on_listing_text(declaration, rule, ctx) -> Optional[Violation]:
    """E-commerce listing text: same presence semantics for now."""
    return presence_check(declaration, rule, ctx)


def format_regex_and_cross_check(declaration, rule, ctx) -> Optional[Violation]:
    """Unit-sale-price: present + (future) cross-check vs MRP*net_qty."""
    fail = presence_check(declaration, rule, ctx)
    if fail is not None:
        return fail
    return None


# ---------------------------------------------------------------------------
# Font-size / legibility validators (Phase 5 metrics)
# ---------------------------------------------------------------------------
def _font_metric_for(ctx, zone_type: str):
    for m in getattr(ctx, "font_metrics", []) or []:
        if m.zone_type == zone_type:
            return m
    return None


def font_height_general_check(metric, rule, min_height_mm: float) -> Optional[Violation]:
    """Rule 7(3): general letter-height check from a measured font metric."""
    if metric is None or not metric.calibrated:
        if metric is None or metric.char_height_px_median == 0.0:
            reason = ("No readable characters in this zone for an automated "
                      "font-size check; flagged for visual review")
            kind = "referral"   # unreadable zone != violation; non-blocking
        else:
            reason = "Font height rule requires a calibrated mm-per-px reference"
            kind = ""
        return Violation(
            rule_id=rule.rule_id, rule_reference=rule.rule_reference,
            field_name="font_size_and_legibility_rules.general_letter_height",
            status="needs_review", severity="medium",
            reason=reason,
            evidence={"char_height_px": metric.char_height_px_median if metric else 0.0,
                      "kind": kind},
        )
    if metric.char_height_mm_median < min_height_mm:
        return Violation(
            rule_id=rule.rule_id, rule_reference=rule.rule_reference,
            field_name="font_size_and_legibility_rules.general_letter_height",
            status="non_compliant", severity="medium",
            reason=f"Font height {metric.char_height_mm_median:.2f} mm below required "
                   f"{min_height_mm} mm",
            evidence={"char_height_mm": metric.char_height_mm_median,
                      "required_mm": min_height_mm},
        )
    return None


def referral_violation(rule, reason: str, severity: str = "medium",
                       evidence: Optional[dict] = None) -> Violation:
    return Violation(rule_id=rule.rule_id, rule_reference=rule.rule_reference,
                     field_name=rule.field_name, status="needs_review",
                     severity=severity, reason=reason, evidence=evidence or {})


REGISTRY = {
    "presence_check": presence_check,
    "presence_and_unit_check": presence_and_unit_check,
    "presence_and_date_format_check": presence_and_date_format_check,
    "format_regex_and_value_check": format_regex_and_value_check,
    "presence_and_contact_format_check": presence_and_contact_format_check,
    "presence_and_ner_check": presence_and_ner_check,
    "conditional_presence_check": conditional_presence_check,
    "presence_check_on_listing_text": presence_check_on_listing_text,
    "format_regex_and_cross_check": format_regex_and_cross_check,
    "disabled": lambda *a, **k: None,
}