"""
Structured output contract for Phases 1-4 (CV/OCR).

This is the intermediate artifact handed to the NLP declaration classifier
(Phase 6) and the rule engine (Phase 7), and ultimately embedded in the final
compliance report (Phase 8).
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class QualityInfo:
    is_usable: bool
    width: int
    height: int
    channels: int
    blur_variance: float
    brightness_mean: float
    darkness_ratio: float
    glare_ratio: float
    warnings: List[str] = field(default_factory=list)


@dataclass
class PreprocessInfo:
    transforms_applied: List[str] = field(default_factory=list)
    deskew_angle: float = 0.0
    perspective_rectified: bool = False


@dataclass
class ZoneInfo:
    zone_type: str
    bbox: List[int]                     # [x, y, w, h]
    text: str = ""
    confidence: float = 0.0
    source: str = "heuristic"
    words: list = field(default_factory=list)   # [{text, confidence, bbox}]


@dataclass
class FullImageOcr:
    text: str
    mean_confidence: float
    word_count: int


@dataclass
class ScanResult:
    status: str = "ok"                  # "ok" | "rejected"
    message: str = ""
    image_width: int = 0
    image_height: int = 0
    quality: QualityInfo = None
    preprocessing: PreprocessInfo = None
    zones: List[ZoneInfo] = field(default_factory=list)
    full_image_ocr: FullImageOcr = None
    warnings: List[str] = field(default_factory=list)


def zones_to_json(zones) -> List[ZoneInfo]:
    out = []
    for z in zones:
        out.append(ZoneInfo(
            zone_type=z.zone_type,
            bbox=list(z.bbox),
            text=z.text,
            confidence=round(z.confidence, 2),
            source=z.source,
            words=[{"text": w.text, "confidence": w.confidence,
                    "bbox": list(w.bbox)} for w in z.words],
        ))
    return out


# ===========================================================================
# Phase 5 - font metrics & calibration
# ===========================================================================


@dataclass
class CalibrationInfo:
    method: str = "none"              # "ean_upc_barcode" | "manual" | "none"
    mm_per_px: float = 0.0
    barcode_type: str = ""
    barcode_value: str = ""
    barcode_bbox: List[int] = field(default_factory=list)   # [x, y, w, h]
    reference_width_mm: float = 0.0
    reference_width_px: float = 0.0
    notes: str = ""


@dataclass
class FontMetricInfo:
    zone_type: str
    char_height_px_median: float = 0.0
    char_height_px_min: float = 0.0
    char_height_px_max: float = 0.0
    char_height_mm_median: float = 0.0       # 0.0 when uncalibrated
    contrast_ratio: float = 0.0
    uppercase_ratio: float = 0.0
    calibrated: bool = False
    warnings: List[str] = field(default_factory=list)


# ===========================================================================
# Phase 6 - extracted declarations (NLP classification output)
# ===========================================================================


@dataclass
class DeclarationInfo:
    field_name: str                     # matches rules DB field_name values
    value: str = ""
    raw_text: str = ""
    confidence: float = 0.0
    method: str = ""                    # "regex" | "spacy" | "merged" | "heuristic"
    source_zone: str = ""               # zone_type or "full_image"
    qualifiers: List[str] = field(default_factory=list)
    rule_id: str = ""


# ===========================================================================
# Phase 7 - violations & final compliance report
# ===========================================================================


@dataclass
class Violation:
    rule_id: str
    rule_reference: str
    field_name: str
    status: str      # compliant | non_compliant | missing | not_applicable | needs_review
    severity: str    # low | medium | high
    reason: str = ""
    evidence: dict = field(default_factory=dict)


@dataclass
class ComplianceStats:
    total_checks: int = 0
    compliant: int = 0
    non_compliant: int = 0
    missing: int = 0
    needs_review: int = 0
    not_applicable: int = 0


@dataclass
class ComplianceReport:
    status: str = "ok"                  # "ok" | "rejected"
    message: str = ""
    compliance_status: str = ""         # compliant | non_compliant | needs_review | not_applicable
    scan: ScanResult = None
    calibration: CalibrationInfo = None
    font_metrics: List[FontMetricInfo] = field(default_factory=list)
    declarations: List[DeclarationInfo] = field(default_factory=list)
    violations: List[Violation] = field(default_factory=list)
    stats: ComplianceStats = None
    warnings: List[str] = field(default_factory=list)
    advice: List[str] = field(default_factory=list)   # operator advisories
                                                      # (e.g. "re-capture needed")