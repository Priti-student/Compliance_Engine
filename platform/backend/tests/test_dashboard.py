"""Dashboard aggregation tests (engine mocked)."""
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


def _create(client, token):
    return client.post(
        "/api/inspections",
        files={"file": ("pkg.png", io.BytesIO(_png_bytes()), "image/png")},
        data={"metadata": '{"category": "food", "product_name": "Biscuit"}'},
        headers=_auth(token),
    ).json()


def test_summary_counts(client, officer_token, mock_engine):
    _create(client, officer_token)
    resp = client.get("/api/dashboard/summary", headers=_auth(officer_token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_inspections"] == 1
    assert body["total_products"] == 1
    assert body["active_officers"] == 1
    assert body["total_violations"] == 3  # 2 missing + 1 non_compliant
    assert body["status_distribution"]["non_compliant"] == 1


def test_status_distribution(client, officer_token, mock_engine):
    _create(client, officer_token)
    rows = client.get(
        "/api/dashboard/status-distribution", headers=_auth(officer_token)
    ).json()
    mapping = {r["status"]: r["count"] for r in rows}
    assert mapping["non_compliant"] == 1
    assert mapping["compliant"] == 0


def test_violation_trend(client, officer_token, mock_engine):
    _create(client, officer_token)
    rows = client.get("/api/dashboard/violation-trend?days=30", headers=_auth(officer_token)).json()
    assert len(rows) == 1
    assert rows[0]["violations"] == 3


def test_top_violations(client, officer_token, mock_engine):
    _create(client, officer_token)
    rows = client.get("/api/dashboard/top-violations", headers=_auth(officer_token)).json()
    assert rows[0]["rule_id"] == "MD-04"
    assert rows[0]["count"] == 1


def test_officer_activity_and_category(client, officer_token, mock_engine):
    _create(client, officer_token)
    activity = client.get("/api/dashboard/officer-activity", headers=_auth(officer_token)).json()
    assert activity[0]["officer"] == "officer"
    assert activity[0]["scans"] == 1

    cats = client.get("/api/dashboard/category-stats", headers=_auth(officer_token)).json()
    assert cats[0]["category"] == "food"
    assert cats[0]["scans"] == 1


def test_recent(client, officer_token, mock_engine):
    _create(client, officer_token)
    recent = client.get("/api/dashboard/recent", headers=_auth(officer_token)).json()
    assert len(recent) == 1
    assert recent[0]["product"]["generic_name"] == "Biscuit"