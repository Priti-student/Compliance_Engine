"""Auth + RBAC tests."""
from app.core.security import hash_password, verify_password


def test_hash_round_trip():
    h = hash_password("Officer@123")
    assert h != "Officer@123"
    assert verify_password("Officer@123", h)
    assert not verify_password("wrong", h)


def test_login_success(client):
    resp = client.post("/api/auth/login", data={"username": "admin", "password": "Admin@123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["user"]["role"] == "admin"


def test_login_wrong_password(client):
    resp = client.post("/api/auth/login", data={"username": "admin", "password": "nope"})
    assert resp.status_code == 401


def test_me(client, admin_token):
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "admin"


def test_raise_on_missing_token(client):
    assert client.get("/api/auth/me").status_code == 401


def test_officer_cannot_list_users(client, officer_token):
    resp = client.get("/api/users", headers={"Authorization": f"Bearer {officer_token}"})
    assert resp.status_code == 403


def test_admin_can_create_user(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.post(
        "/api/users",
        json={
            "username": "officer2",
            "full_name": "Second Officer",
            "email": "officer2@x.in",
            "password": "Officer@123",
            "role": "officer",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["username"] == "officer2"


def test_admin_reset_password(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.post(
        "/api/users/3/reset-password", json={"new_password": "Fresh@12345"}, headers=headers
    )
    assert resp.status_code == 200
    # old password no longer works, new one does
    assert (
        client.post("/api/auth/login", data={"username": "officer", "password": "Officer@123"})
    ).status_code == 401
    assert (
        client.post("/api/auth/login", data={"username": "officer", "password": "Fresh@12345"})
    ).status_code == 200