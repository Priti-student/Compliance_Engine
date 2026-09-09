"""FastAPI endpoint tests (Phase 0-4 integration surface)."""
import pytest
from fastapi.testclient import TestClient

from compliance_engine.api import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_health(client):
    resp = client.get("/cv/health")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "ok"
    assert "opencv_version" in payload
    assert "tesseract_version" in payload


def test_scan_accepted_for_image_upload(client, sample_images):
    with open(sample_images[0], "rb") as f:
        resp = client.post(
            "/cv/scan",
            files={"file": ("package_001.jpg", f, "image/jpeg")},
        )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "ok"
    assert payload["zones"]
    assert payload["full_image_ocr"]["word_count"] > 0


def test_scan_accepts_full_image_upload(client, sample_images):
    """The /compliance/scan endpoint returns a full ComplianceReport."""
    with open(sample_images[0], "rb") as f:
        resp = client.post(
            "/compliance/scan",
            files={"file": ("package_001.jpg", f, "image/jpeg")},
        )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "ok"
    assert "compliance_status" in payload
    assert "declarations" in payload
    assert payload["declarations"]
    assert "violations" in payload
    assert payload["stats"]["total_checks"] == len(payload["violations"])
    assert payload["calibration"]["method"] in ("none", "ean_upc_barcode", "manual")


def test_scan_rejects_non_image_content_type(client):
    resp = client.post(
        "/cv/scan",
        files={"file": ("note.txt", b"not an image", "text/plain")},
    )
    assert resp.status_code == 415


def test_scan_rejects_empty_upload(client):
    resp = client.post(
        "/cv/scan",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert resp.status_code in (400, 422)