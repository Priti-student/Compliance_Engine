"""End-to-end Phase 1-4 pipeline tests (structured ScanResult output)."""
import numpy as np
import pytest

from compliance_engine.pipeline import run_scan
from compliance_engine.schema import ScanResult


def test_run_scan_returns_structured_result(scan_package_001):
    result = scan_package_001
    assert isinstance(result, ScanResult)
    assert result.status == "ok"
    assert result.quality.is_usable is True
    assert result.preprocessing is not None
    assert len(result.zones) > 0
    assert result.full_image_ocr is not None
    assert result.full_image_ocr.word_count > 0


def test_run_scan_zone_contains_words(scan_package_001):
    assert any(z.words for z in scan_package_001.zones)


def test_run_scan_rejects_invalid_file(tmp_path):
    junk = tmp_path / "not_an_image.txt"
    junk.write_bytes(b"hello world, not an image")
    result = run_scan(str(junk))
    assert result.status == "rejected"


def test_run_scan_accepts_numpy_array(sample_images):
    from compliance_engine.cv.quality import load_image
    array = load_image(sample_images[0])
    assert isinstance(array, np.ndarray)
    result = run_scan(array)
    assert result.status == "ok"