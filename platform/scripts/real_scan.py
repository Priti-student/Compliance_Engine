"""Real end-to-end scan: platform upload -> engine OCR -> persisted report.

Uses one of the engine's own sample product images (override via argv[1]).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = ROOT / "Compliance_Engine_CV_NLP"
SAMPLE = SAMPLES / (sys.argv[1] if len(sys.argv) > 1 else "package_001.jpg")
BASE = "http://127.0.0.1:8001"


def main() -> int:
    with httpx.Client(base_url=BASE, timeout=180) as c:
        r = c.get("/api/health")
        print("platform-health:", r.json())

        r = c.post("/api/auth/login", data={"username": "officer", "password": "Officer@123"})
        token = r.json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}
        print("login:", r.status_code)

        data = SAMPLE.read_bytes()
        files = {"file": (SAMPLE.name, data, "image/jpeg")}
        meta = {
            "product_name": "Scan via engine",
            "category": "food",
            "remarks": f"Real engine scan of {SAMPLE.name}",
        }
        r = c.post(
            "/api/inspections",
            files=files,
            data={"metadata": json.dumps(meta)},
            headers=h,
            timeout=180,
        )
        print("scan status:", r.status_code, "| image:", SAMPLE.name)
        if r.status_code != 201:
            print(r.text[:2000])
            return 1
        body = r.json()
        print("token:", body["token"])
        print("compliance_status:", body["compliance_status"])
        print("stats:", body["stats"])
        print("declarations:", len(body["declarations"]), "| violations:", len(body["violations"]),
              "| font_metrics:", len(body["font_metrics"]))
        print("reports:", [(x["report_type"], x["size_bytes"]) for x in body["reports"]])
        print("product from OCR:", (body.get("product") or {}).get("generic_name"))

        tok = body["token"]
        for kind, magic in (("pdf", b"%PDF"), ("xlsx", b"PK")):
            r = c.get(f"/api/reports/{tok}/{kind}", headers=h)
            ok = r.content.startswith(magic)
            print(f"download {kind}:", r.status_code, "magic-ok" if ok else "BAD-MAGIC")

        r = c.get("/api/dashboard/summary", headers=h)
        print("dashboard total inspections:", r.json()["total_inspections"])
        return 0 if r.status_code == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())