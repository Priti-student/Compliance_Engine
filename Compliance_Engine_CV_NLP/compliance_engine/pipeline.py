"""
Phase 1-7 pipeline orchestration.

    load -> quality gate -> preprocess -> zone detection -> per-zone OCR
    -> whole-image OCR fallback -> ScanResult JSON
    -> font metrics & calibration (Phase 5)
    -> declaration extraction (Phase 6)
    -> rule-engine compliance evaluation (Phase 7)
    -> ComplianceReport JSON

run_scan() returns the Phase 1-4 ScanResult; run_full_pipeline() chains
Phases 5-7 and returns the end-to-end ComplianceReport consumed by the
report/dashboard/DB teammates.
"""
from typing import List, Optional, Union

import numpy as np

from compliance_engine import config
from compliance_engine.cv.preprocessing import preprocess
from compliance_engine.cv.quality import assess_quality, load_image
from compliance_engine.cv.zone_detection import detect_zones
from compliance_engine.cv.ocr_engine import ocr_zone, ocr_full_image
from compliance_engine.cv.font_metrics import (
    get_calibration,
    manual_calibration,
    measure_zone_font,
)
from compliance_engine.nlp.declaration_extractor import extract_declarations
from compliance_engine.rules.rule_engine import RuleEngine, overall_status
from compliance_engine.schema import (
    ComplianceReport,
    FullImageOcr,
    PreprocessInfo,
    QualityInfo,
    ScanResult,
    ZoneInfo,
    zones_to_json,
)


def run_scan(image_path_or_bytes: Union[str, bytes, np.ndarray]) -> ScanResult:
    """Run Phases 1-4 on one product image and return the structured result.

    For a CBA-contract scan of an image file path, raw bytes, or a decoded
    RGB numpy array.
    """
    if isinstance(image_path_or_bytes, np.ndarray):
        image = image_path_or_bytes
    else:
        image = load_image(image_path_or_bytes)

    if image is None:
        return ScanResult(
            status="rejected",
            message="Could not decode the uploaded file as an image.",
        )

    h, w = image.shape[:2]
    result = ScanResult(image_width=w, image_height=h)

    # --- Phase 1: quality gate ---
    quality = assess_quality(image)
    result.quality = QualityInfo(
        is_usable=quality.is_usable, width=quality.width, height=quality.height,
        channels=quality.channels, blur_variance=round(quality.blur_variance, 2),
        brightness_mean=round(quality.brightness_mean, 2),
        darkness_ratio=round(quality.darkness_ratio, 4),
        glare_ratio=round(quality.glare_ratio, 4),
        warnings=quality.warnings,
    )
    if not quality.is_usable:
        result.status = "rejected"
        result.message = "Image failed the quality gate; flag for re-capture."
        result.warnings = quality.warnings
        return result

    # --- Phase 2: preprocessing ---
    pre = preprocess(image)
    result.preprocessing = PreprocessInfo(
        transforms_applied=pre.transforms_applied,
        deskew_angle=round(pre.deskew_angle, 2),
        perspective_rectified=pre.perspective_rectified,
    )

    # --- Phase 3: zone detection ---
    zone_result = detect_zones(pre.image)
    warnings = list(zone_result.warnings)

    # --- Phase 4: OCR (per-zone focused pass + whole-image fallback) ---
    zones_with_words: List[ZoneInfo] = []
    for zone in zone_result.zones:
        x, y, w_, h_ = zone.bbox
        pad = 6
        x0, y0 = max(0, x - pad), max(0, y - pad)
        x1, y1 = min(pre.image.shape[1], x + w_ + pad), min(pre.image.shape[0], y + h_ + pad)
        crop = pre.image[y0:y1, x0:x1]
        ocr = ocr_zone(crop, zone.zone_type)
        for msg in ocr.warnings:
            warnings.append(msg)
        zones_with_words.append(ZoneInfo(
            zone_type=zone.zone_type,
            bbox=[x, y, w_, h_],
            text=ocr.text if ocr.text.strip() else zone.text,
            confidence=round(ocr.mean_confidence, 2) if ocr.words else
            round(zone.confidence, 2),
            source=zone.source,
            words=[{"text": wrd.text, "confidence": wrd.confidence,
                    "bbox": list(wrd.bbox)} for wrd in ocr.words],
        ))

    full_ocr = ocr_full_image(pre.image)
    result.zones = zones_with_words
    result.full_image_ocr = FullImageOcr(
        text=full_ocr.text,
        mean_confidence=round(full_ocr.mean_confidence, 2),
        word_count=len(full_ocr.words),
    )
    result.warnings = warnings
    return result


def run_full_pipeline(
    image_path_or_bytes: Union[str, bytes, np.ndarray],
    metadata: Optional[dict] = None,
    calibration_mm_per_px: Optional[float] = None,
) -> ComplianceReport:
    """Run Phases 1-7: scan -> font metrics -> declarations -> rule engine.

    Returns a ComplianceReport (scan result + calibration + font metrics +
    extracted declarations + violations + stats + overall status). This is the
    main integration endpoint for report/dashboard/DB teammates.
    """
    report = ComplianceReport()
    scan = run_scan(image_path_or_bytes)
    if scan.status == "rejected":
        report.status = "rejected"
        report.message = scan.message
        report.warnings = scan.warnings
        return report
    report.scan = scan

    # --- Phase 5: calibration (barcode when available, else manual/None) ---
    image = None
    if isinstance(image_path_or_bytes, np.ndarray):
        image = image_path_or_bytes
    else:
        image = load_image(image_path_or_bytes)

    if calibration_mm_per_px is not None:
        report.calibration = manual_calibration(calibration_mm_per_px)
    else:
        report.calibration = get_calibration(image)

    # --- Phase 5: font metrics per zone ---
    for zone in scan.zones or []:
        x, y, w, h = zone.bbox
        crop = image[y:y + h, x:x + w]
        metric = measure_zone_font(
            crop, zone.text,
            mm_per_px=report.calibration.mm_per_px or None,
            psm=(config.SHORT_LINE_OCR_PSM
                 if zone.zone_type in config.SHORT_LINE_ZONE_TYPES
                 else config.DEFAULT_OCR_PSM),
        )
        metric.zone_type = zone.zone_type
        report.font_metrics.append(metric)

    # --- Phase 6: declaration extraction ---
    report.declarations = extract_declarations(scan)

    # --- Phase 7: rule engine ---
    engine = RuleEngine()
    violations, stats = engine.evaluate(
        report.declarations,
        report.font_metrics,
        calibration_mm_per_px=report.calibration.mm_per_px,
        metadata=metadata or {},
    )
    report.violations = violations
    report.stats = stats
    report.compliance_status = overall_status(stats, violations)

    # --- Operator advice: low-quality captures shouldn't be read as a verdict.
    # A high glare ratio or very low OCR confidence means the label wasn't
    # reliably read -- the honest move is to re-photograph, not trust a
    # 'non_compliant' verdict built on garbage OCR.
    quality = scan.quality
    if quality is not None:
        if quality.glare_ratio > config.HIGH_GLARE_RATIO:
            report.advice.append(
                f"Re-capture advised: high glare ({quality.glare_ratio:.0%} of "
                "pixels) may hide declaration text."
            )
    full_ocr = scan.full_image_ocr
    if full_ocr is not None and full_ocr.mean_confidence < config.LOW_OCR_CONFIDENCE:
        report.advice.append(
            f"Re-capture advised: low OCR confidence "
            f"({full_ocr.mean_confidence:.0f}/100) means text was not read "
            "reliably."
        )
    return report


# Re-exported pipeline entrypoints.
__all__ = ["run_scan", "run_full_pipeline"]