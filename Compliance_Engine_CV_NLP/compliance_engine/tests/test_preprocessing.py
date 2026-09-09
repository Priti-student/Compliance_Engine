"""Phase 2 - preprocessing tests."""
from compliance_engine.cv.preprocessing import preprocess
from compliance_engine.cv.quality import load_image


def test_preprocess_runs_and_returns_rgb(sample_images):
    for path in sample_images:
        image = load_image(path)
        result = preprocess(image)
        assert result.image.ndim == 3
        assert result.image.shape[2] == 3
        assert isinstance(result.transforms_applied, list)
        assert "CLAHE" in result.transforms_applied


def test_preprocess_keeps_orientation(sample_images):
    image = load_image(sample_images[0])
    result = preprocess(image)
    # Deskew rotation never flips the image.
    assert result.image.shape[0] == image.shape[0]
    assert result.image.shape[1] == image.shape[1]