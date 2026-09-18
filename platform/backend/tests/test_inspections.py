"""Inspection flow tests (engine mocked)."""
import io


def _png_bytes() -> bytes:
    """A real, decodable 16x16 PNG generated with Pillow."""
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (16, 16), (60, 130, 200)).save(buf, "PNG")
    return buf.getvalue()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_upload_requires_image(client, officer_token):
    resp = client.post(
        "/api/inspections",
        files={"file": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
        headers=_auth(officer_token),
    )
    assert resp.status_code == 400


def test_scan_creates_inspection(client, officer_token, mock_engine):
    resp = client.post(
        "/api/inspections",
        files={"file": ("pkg.png", io.BytesIO(_png_bytes()), "image/png")},
        data={"metadata": '{"category": "food", "product_name": "Biscuit"}'},
        headers=_auth(officer_token),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()

    assert body["token"]
    assert body["compliance_status"] == "non_compliant"
    assert body["product"]["generic_name"] == "Biscuit"
    assert len(body["declarations"]) == 2
    assert len(body["violations"]) == 1
    assert body["violations"][0]["rule_id"] == "MD-04"
    assert any(r["report_type"] == "pdf" for r in body["reports"])


def test_list_and_get_inspection(client, officer_token, mock_engine):
    h = _auth(officer_token)
    created = client.post(
        "/api/inspections",
        files={"file": ("pkg.png", io.BytesIO(_png_bytes()), "image/png")},
        headers=h,
    ).json()
    token = created["token"]

    listing = client.get("/api/inspections?q=Biscuit", headers=h)
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    assert listing.json()["items"][0]["token"] == token

    detail = client.get(f"/api/inspections/{token}", headers=h)
    assert detail.status_code == 200
    assert detail.json()["stats"]["missing"] == 2


def test_evidence_upload_and_download(client, officer_token, mock_engine):
    h = _auth(officer_token)
    token = client.post(
        "/api/inspections",
        files={"file": ("pkg.png", io.BytesIO(_png_bytes()), "image/png")},
        headers=h,
    ).json()["token"]

    resp = client.post(
        f"/api/inspections/{token}/evidence",
        files=[("files", ("exhibit.jpg", io.BytesIO(_png_bytes()), "image/jpeg"))],
        headers=h,
    )
    assert resp.status_code == 201, resp.text
    ev_id = resp.json()["evidence"][0]["id"]

    img = client.get(f"/api/inspections/{token}/image?annotated=true", headers=h)
    assert img.status_code == 200
    assert img.headers["content-type"].startswith("image/jpeg")


def test_image_accessible_with_query_token(client, officer_token, mock_engine):
    token = client.post(
        "/api/inspections",
        files={"file": ("pkg.png", io.BytesIO(_png_bytes()), "image/png")},
        headers=_auth(officer_token),
    ).json()["token"]
    resp = client.get(f"/api/inspections/{token}/image?access_token={officer_token}")
    assert resp.status_code == 200


def test_non_reviewer_cannot_approve(client, officer_token, mock_engine):
    h = _auth(officer_token)
    token = client.post(
        "/api/inspections",
        files={"file": ("pkg.png", io.BytesIO(_png_bytes()), "image/png")},
        headers=h,
    ).json()["token"]
    resp = client.patch(
        f"/api/inspections/{token}",
        json={"workflow_status": "approved", "remarks": "ok"},
        headers=h,
    )
    assert resp.status_code == 403


def test_reviewer_can_approve(client, reviewer_token, officer_token, mock_engine):
    token = client.post(
        "/api/inspections",
        files={"file": ("pkg.png", io.BytesIO(_png_bytes()), "image/png")},
        headers=_auth(officer_token),
    ).json()["token"]

    resp = client.patch(
        f"/api/inspections/{token}",
        json={"workflow_status": "approved", "remarks": "all good"},
        headers=_auth(reviewer_token),
    )
    assert resp.status_code == 200
    assert resp.json()["workflow_status"] == "approved"
    assert resp.json()["reviewer"]["username"] == "reviewer"