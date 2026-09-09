"""Phase 5 - font metrics & calibration tests."""
import os

import numpy as np
import pytest

from compliance_engine.cv.font_metrics import (
    detect_barcode,
    get_calibration,
    manual_calibration,
    measure_zone_font,
)
from compliance_engine.cv.quality import load_image

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def test_barcode_detected_on_wheet():
    """Wheet.jpeg contains a decodable UPC-A barcode (verified earlier)."""
    img = load_image(os.path.join(_REPO_ROOT, "Wheet.jpeg"))
    info = detect_barcode(img)
    assert info is not None
    assert info["barcode_type"].upper() in ("EAN_13", "UPC_A", "EAN13", "UPC-A")
    assert info["width_px"] > 5
    assert len(info["bbox"]) == 4


def test_no_barcode_found_on_package_001():
    img = load_image(os.path.join(_REPO_ROOT, "package_001.jpg"))
    assert detect_barcode(img) is None


def test_get_calibration_returns_mm_per_px_on_wheet():
    img = load_image(os.path.join(_REPO_ROOT, "Wheet.jpeg"))
    cal = get_calibration(img)
    assert cal.method == "ean_upc_barcode"
    assert cal.mm_per_px > 0
    assert cal.barcode_value  # decoded string


def test_manual_calibration():
    cal = manual_calibration(0.05)
    assert cal.method == "manual"
    assert cal.mm_per_px == pytest.approx(0.05)


def test_measure_zone_font_returns_metrics(sample_images):
    img = load_image(sample_images[0])
    # Fake a small text-like crop (a white patch with a dark bar).
    crop = np.zeros((40, 200, 3), dtype=np.uint8) + 255
    crop[15:25, 20:30] = 0    # a bar
    metric = measure_zone_font(crop, "MRP 20.00")
    assert metric.char_height_px_median >= 2.0
    assert metric.char_height_px_min >= 1.0
    assert metric.contrast_ratio > 0.0


def test_measure_zone_font_calibrated_mm():
    crop = np.zeros((60, 200, 3), dtype=np.uint8) + 255
    crop[20:40, 20:40] = 0
    metric = measure_zone_font(crop, "NET 50 g", mm_per_px=0.1)
    assert metric.calibrated is True
    assert metric.char_height_mm_median > 0.0


def test_measure_zone_font_empty_crop():
    metric = measure_zone_font(None, "")
    assert metric.warnings
    assert metric.char_height_px_median == 0.0