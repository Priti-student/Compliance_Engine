"""Probe /api/auth/me: 401 without token, 200 with a fresh login token."""
import httpx

base = "http://127.0.0.1:8001"
with httpx.Client(base_url=base, timeout=15) as c:
    r = c.get("/api/auth/me")
    print("no-token:", r.status_code)
    login = c.post("/api/auth/login", data={"username": "officer", "password": "Officer@123"})
    token = login.json()["access_token"]
    r = c.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    print("with-token:", r.status_code, r.json()["username"])