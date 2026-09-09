"""Phase 3 - zone detection tests against known sample images."""
from compliance_engine.cv.preprocessing import preprocess
from compliance_engine.cv.quality import load_image
from compliance_engine.cv.zone_detection import detect_zones
import pytest


def _zone_types(path):
    image = load_image(path)
    result = detect_zones(preprocess(image).image)
    return {z.zone_type for z in result.zones}


def test_package_001_detects_declaration_zones(sample_images):
    """Known front label: MRP, net qty, dates, batch, manufacturer."""
    types = _zone_types(sample_images[0])
    assert "mrp_block" in types
    assert "net_qty_block" in types
    assert "mfg_date_block" in types
    assert "expiry_date_block" in types
    assert "manufacturer_address_block" in types


def test_lays_detects_key_zones(sample_images):
    """Lays front-of-pack: MRP, net qty, FSSAI licence."""
    types = _zone_types(sample_images[3])
    assert "mrp_block" in types
    assert "net_qty_block" in types
    assert "fssai_block" in types


def test_zones_have_valid_bboxes(sample_images):
    image = load_image(sample_images[0])
    result = detect_zones(preprocess(image).image)
    h, w = preprocess(image).image.shape[:2]
    for zone in result.zones:
        x, y, zw, zh = zone.bbox
        assert x >= 0 and y >= 0
        assert x + zw <= w and y + zh <= h
        assert zw > 0 and zh > 0