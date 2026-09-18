"""Self-contained end-to-end check against the real stack.

Spawns uvicorn (real PostgreSQL, real storage backend), waits until it
responds, exercises the whole API surface, then shuts the server down.

Usage:  platform\\venv\\Scripts\\python.exe platform\\scripts\\run_e2e.py
Requires: seeded database (python -m app.services.seed) and reachable Postgres.
"""
from __future__ import annotations

import subprocess
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / "venv" / "Scripts" / "python.exe"
BACKEND = ROOT / "backend"
BASE = "http://127.0.0.1:8001"
FAILURES: list[str] = []


def check(name: str, cond: bool, extra: str = "") -> None:
    tag = "ok " if cond else "FAIL"
    print(f"[{tag}] {name} {extra}")
    if not cond:
        FAILURES.append(name)


def main() -> int:
    log = open(ROOT / "server.log", "w", encoding="utf-8")
    err = open(ROOT / "server.err.log", "w", encoding="utf-8")
    proc = subprocess.Popen(
        [str(PY), "-m", "uvicorn", "app.main:app", "--port", "8001"],
        cwd=str(BACKEND), stdout=log, stderr=err,
    )
    try:
        with httpx.Client(base_url=BASE, timeout=60) as c:
            deadline = time.time() + 45
            while True:
                try:
                    r = c.get("/api/health")
                    if r.status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                if time.time() > deadline:
                    check("server-startup", False, err.read()[:800])
                    return 1
                time.sleep(1)

            r = c.get("/api/health")
            b = r.json()
            check("health-200", r.status_code == 200, f"engine_online={b['engine_online']}")
            check("health-db-ok", b["database"] == "ok")

            r = c.post("/api/auth/login", data={"username": "officer", "password": "Officer@123"})
            check("login-officer", r.status_code == 200)
            token = r.json()["access_token"]
            h = {"Authorization": f"Bearer {token}"}

            r = c.get("/api/auth/me", headers=h)
            check("auth-me", r.status_code == 200 and r.json()["username"] == "officer")
            r = c.get("/api/users", headers=h)
            check("rbac-officer-denied-users", r.status_code == 403)

            r = c.get("/api/dashboard/summary", headers=h)
            b = r.json()
            check("dashboard-summary", r.status_code == 200 and b["total_inspections"] >= 5)
            r = c.get("/api/dashboard/violation-trend?days=30", headers=h)
            check("dashboard-trend", r.status_code == 200 and isinstance(r.json(), list))
            r = c.get("/api/dashboard/top-violations", headers=h)
            check("dashboard-top-violations", r.status_code == 200 and len(r.json()) > 0)

            r = c.get("/api/search?q=Wheet", headers=h)
            check("search-q", r.status_code == 200 and r.json()["total"] >= 1)
            r = c.get("/api/search/suggest?q=bri", headers=h)
            check("search-suggest", r.status_code == 200)

            r = c.get("/api/search?from_date=2020-01-01&to_date=2035-01-01", headers=h)
            check("search-date-range", r.status_code == 200 and r.json()["total"] >= 1)
            r = c.get("/api/search?from_date=not-a-date", headers=h)
            check("search-bad-date-400", r.status_code == 400)

            r = c.get("/api/inspections?size=5", headers=h)
            items = r.json()["items"]
            check("inspections-list", len(items) >= 5)
            token_insp = items[0]["token"]

            r = c.get(f"/api/inspections/{token_insp}", headers=h)
            detail = r.json()
            check("inspection-detail", r.status_code == 200 and detail["token"] == token_insp)
            check("inspection-has-declarations", len(detail["declarations"]) > 0)

            r = c.get(f"/api/inspections/{token_insp}/image?annotated=true", headers=h)
            check("image-annotated", r.status_code == 200 and r.headers["content-type"] == "image/jpeg")

            r = c.get(f"/api/reports/{token_insp}/pdf", headers=h)
            check("report-pdf", r.status_code == 200 and r.content.startswith(b"%PDF"))
            r = c.get(f"/api/reports/{token_insp}/xlsx", headers=h)
            check("report-xlsx", r.status_code == 200 and r.content[:2] == b"PK")
            r = c.get(f"/api/reports/{token_insp}/json", headers=h)
            check("report-json", r.status_code == 200 and r.json()["meta"]["token"] == token_insp)

            r = c.post("/api/auth/login", data={"username": "reviewer", "password": "Reviewer@123"})
            h_rev = {"Authorization": f"Bearer {r.json()['access_token']}"}
            r = c.patch(
                f"/api/inspections/{token_insp}",
                json={"workflow_status": "approved", "remarks": "E2E approved"},
                headers=h_rev,
            )
            check("reviewer-approve", r.status_code == 200 and r.json()["workflow_status"] == "approved")

            r = c.get("/api/rules", headers=h_rev)
            check("rules-db", r.status_code == 200 and "mandatory_declarations" in r.json())
            r = c.get("/api/rules/health", headers=h_rev)
            check("rules-health", r.status_code == 200)

            r = c.get("/api/products?size=5", headers=h)
            check("products-list", r.status_code == 200 and r.json()["total"] >= 1)

            r = c.post("/api/inspections/from-demo", json={"source": "package_001.json"}, headers=h)
            check("demo-import", r.status_code == 201, f"token={r.json().get('token')}")

            print(f"\n{len(FAILURES)} failure(s)" if FAILURES else "\nALL CHECKS PASSED")
            return 1 if FAILURES else 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        log.close()
        err.close()


if __name__ == "__main__":
    raise SystemExit(main())