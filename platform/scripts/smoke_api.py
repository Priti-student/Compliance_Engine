"""End-to-end smoke test against a live platform backend (port 8001).

Requires:  platform\\venv\\Scripts\\python.exe -m uvicorn app.main:app --port 8001
Plus a seeded database (run seed first). The CV/OCR engine on :8000 is optional;
when offline, /api/health reports engine_online=false and demo import still works.
"""
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

BASE = "http://127.0.0.1:8001"


def main() -> int:
    with httpx.Client(base_url=BASE, timeout=120) as c:
        r = c.get("/api/health")
        print("[health]", r.status_code, r.json())

        r = c.post("/api/auth/login", data={"username": "officer", "password": "Officer@123"})
        assert r.status_code == 200, r.text
        token = r.json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}
        print("[login] ok, role=", r.json()["user"]["role"])

        r = c.get("/api/dashboard/summary", headers=h)
        body = r.json()
        print("[dashboard/summary]", r.status_code, "total:", body["total_inspections"],
              "rate%:", body["compliance_rate_pct"])

        r = c.get("/api/dashboard/violation-trend?days=30", headers=h)
        print("[violation-trend]", r.status_code, "days:", len(r.json()))

        r = c.get("/api/search?q=Wheet", headers=h)
        print("[search q=Wheet]", r.status_code, "total:", r.json()["total"])

        r = c.get("/api/inspections?size=5", headers=h)
        items = r.json()["items"]
        print("[inspections]", len(items), "rows")
        token_insp = items[0]["token"] if items else None

        r = c.get("/api/reports/inspection/" + token_insp, headers=h)
        print("[reports list]", r.status_code, r.json())

        r = c.get(f"/api/inspections/{token_insp}/image?annotated=true", headers=h)
        print("[image annotated]", r.status_code, r.headers.get("content-type"), len(r.content))

        for kind in ("pdf", "xlsx", "json"):
            r = c.get(f"/api/reports/{token_insp}/{kind}", headers=h)
            print(f"[report {kind}]", r.status_code, len(r.content))

        r = c.get("/api/products?size=5", headers=h)
        print("[products]", r.status_code, "total:", r.json()["total"])

        r = c.get("/api/rules", headers=h)
        print("[rules]", r.status_code, "version:", r.json()["database_meta"]["version"])

        r = c.post("/api/inspections/from-demo", json={"source": "package_001.json"}, headers=h)
        print("[demo import]", r.status_code, r.json())
        return 0


if __name__ == "__main__":
    raise SystemExit(main())