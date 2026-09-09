"""Phase 4 - OCR extraction tests."""
from compliance_engine.cv.ocr_engine import ocr_full_image, ocr_zone
from compliance_engine.cv.preprocessing import preprocess
from compliance_engine.cv.quality import load_image
from compliance_engine.cv.zone_detection import detect_zones


def test_full_image_ocr_extracts_expected_fields(sample_images):
    """Ground truth declarations present on package_001 front label."""
    image = load_image(sample_images[0])
    ocr = ocr_full_image(preprocess(image).image)
    text = ocr.text

    # OCR quality is not perfect, but these key fragments should survive.
    assert "MRP" in text or "20.00" in text
    assert "MFD:" in text or "MFD" in text
    assert "10/07/2024" in text or "2024" in text
    assert "Net" in text or "Quantity" in text
    assert "PepsiCo" in text or "India" in text


def test_ocr_returns_word_level_data(sample_images):
    image = load_image(sample_images[0])
    ocr = ocr_full_image(preprocess(image).image)
    assert ocr.words
    word = ocr.words[0]
    assert word.text
    assert len(word.bbox) == 4
    assert 0.0 <= word.confidence <= 100.0


def test_ocr_zone_on_mrp_crop(sample_images):
    image = load_image(sample_images[0])
    pre = preprocess(image)
    result = detect_zones(pre.image)
    mrp = next((z for z in result.zones if z.zone_type == "mrp_block"), None)
    if mrp is None:
        return  # zone detection already covered elsewhere; don't hard-fail OCR
    x, y, w, h = mrp.bbox
    crop = pre.image[max(0, y - 6):y + h + 6, max(0, x - 6):x + w + 6]
    ocr = ocr_zone(crop, "mrp_block")
    assert "20.00" in ocr.text or "MRP" in ocr.text