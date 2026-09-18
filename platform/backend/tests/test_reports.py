"""Report generation/download tests."""
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


def _make(client, token, mock_engine):
    return client.post(
        "/api/inspections",
        files={"file": ("pkg.png", io.BytesIO(_png_bytes()), "image/png")},
        headers=_auth(token),
    ).json()["token"]


def test_artifacts_generated_on_scan(client, officer_token, mock_engine):
    created = client.post(
        "/api/inspections",
        files={"file": ("pkg.png", io.BytesIO(_png_bytes()), "image/png")},
        headers=_auth(officer_token),
    ).json()
    kinds = {r["report_type"] for r in created["reports"]}
    assert kinds == {"pdf", "xlsx", "json"}


def test_download_pdf(client, officer_token, mock_engine):
    token = _make(client, officer_token, mock_engine)
    resp = client.get(f"/api/reports/{token}/pdf", headers=_auth(officer_token))
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")


def test_download_xlsx(client, officer_token, mock_engine):
    token = _make(client, officer_token, mock_engine)
    resp = client.get(f"/api/reports/{token}/xlsx", headers=_auth(officer_token))
    assert resp.status_code == 200
    assert resp.content[:2] == b"PK"  # xlsx is a zip


def test_download_json(client, officer_token, mock_engine):
    token = _make(client, officer_token, mock_engine)
    resp = client.get(f"/api/reports/{token}/json", headers=_auth(officer_token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["token"] == token
    assert body["compliance_report"]["compliance_status"] == "non_compliant"


def test_download_requires_auth(client, officer_token, mock_engine):
    token = _make(client, officer_token, mock_engine)
    assert client.get(f"/api/reports/{token}/pdf").status_code == 401


def test_regenerate_report(client, officer_token, mock_engine):
    token = _make(client, officer_token, mock_engine)
    resp = client.post(
        f"/api/reports/{token}",
        json={"report_type": "pdf"},
        headers=_auth(officer_token),
    )
    assert resp.status_code == 200
    assert resp.json()["artifact"]["report_type"] == "pdf"