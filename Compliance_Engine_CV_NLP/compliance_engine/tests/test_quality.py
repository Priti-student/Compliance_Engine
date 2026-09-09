"""Phase 1 - quality gate tests."""
from compliance_engine.cv.quality import assess_quality, load_image


def test_load_all_sample_images_decodes(sample_images):
    for path in sample_images:
        assert load_image(path) is not None, f"failed to decode {path}"


def test_quality_report_shape(sample_images):
    image = load_image(sample_images[0])
    report = assess_quality(image)
    assert report.width > 0 and report.height > 0
    assert report.is_usable in (True, False)
    assert report.blur_variance >= 0.0
    assert 0.0 <= report.brightness_mean <= 255.0
    assert isinstance(report.warnings, list)


def test_quality_rejects_garbage_bytes():
    report = assess_quality(None)
    assert report.is_usable is False
    assert report.warnings


def test_load_image_returns_none_for_junk(tmp_path):
    junk = tmp_path / "junk.bin"
    junk.write_bytes(b"this is not an image")
    assert load_image(str(junk)) is None