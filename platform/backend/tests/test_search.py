"""Repository search tests (engine mocked)."""
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


def _create(client, token, product_name="Biscuit"):
    return client.post(
        "/api/inspections",
        files={"file": ("pkg.png", io.BytesIO(_png_bytes()), "image/png")},
        data={"metadata": f'{{"category": "food", "product_name": "{product_name}"}}'},
        headers=_auth(token),
    ).json()


def test_search_by_product_name(client, officer_token, mock_engine):
    _create(client, officer_token, "Biscuit")
    _create(client, officer_token, "Shampoo")
    resp = client.get("/api/search?q=Shampoo", headers=_auth(officer_token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["product"]["generic_name"] == "Shampoo"


def test_search_filter_by_status(client, officer_token, mock_engine):
    _create(client, officer_token, "Biscuit")
    resp = client.get(
        "/api/search?compliance_status=compliant", headers=_auth(officer_token)
    )
    assert resp.json()["total"] == 0
    resp = client.get(
        "/api/search?compliance_status=non_compliant", headers=_auth(officer_token)
    )
    assert resp.json()["total"] == 1


def test_search_filter_by_category_and_pagination(client, officer_token, mock_engine):
    for i in range(25):
        _create(client, officer_token, f"Product {i}")
    resp = client.get(
        "/api/search?category=food&page=1&size=10", headers=_auth(officer_token)
    )
    body = resp.json()
    assert body["total"] == 25
    assert len(body["items"]) == 10

    page2 = client.get(
        "/api/search?category=food&page=3&size=10", headers=_auth(officer_token)
    ).json()
    assert len(page2["items"]) == 5


def test_search_suggest(client, officer_token, mock_engine):
    _create(client, officer_token, "Britannia Biscuit")
    resp = client.get("/api/search/suggest?q=bri", headers=_auth(officer_token))
    assert "Britannia Biscuit" in resp.json()["suggestions"]


def test_search_empty_repo(client, officer_token):
    resp = client.get("/api/search?q=anything", headers=_auth(officer_token))
    assert resp.status_code == 200
    assert resp.json()["total"] == 0