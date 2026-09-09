"""Smoke: exercise Phase 8-10 endpoints (report, repository, dashboard)."""
import json
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from fastapi.testclient import TestClient

from compliance_engine.api import app
from compliance_engine.pipeline import run_full_pipeline

client = TestClient(app)

# 1. Run the full pipeline for package_001 and save into the repo with operator metadata.
report = run_full_pipeline("package_001.jpg")
from compliance_engine.api import _persist_scan
row = _persist_scan(report, metadata={"officer": "inspector_a", "scan_id": "pkg001"})
print("saved row:", {k: row[k] for k in ("scan_id", "compliance_status", "missing")})

# 2. Report export endpoint (writes PDF/XLSX/JSON under data/reports).
with open("package_001.jpg", "rb") as fh:
    resp = client.post(
        "/compliance/scan/report",
        files={"file": ("package_001.jpg", fh, "image/jpeg")},
        data={"metadata": json.dumps({"scan_id": "pkg001"})},
    )
print("report endpoint:", resp.status_code, resp.json().get("compliance_status"),
      "| files:", resp.json().get("files"))

# 3. Repository list / get / search / stats.
print("list count:", len(client.get("/repository/scans?limit=10").json()))
scan_id = row["scan_id"]
print("get by id:", client.get(f"/repository/scans/{scan_id}").status_code)
print("search 'mrp':", len(client.get("/repository/search", params={"q": "pkg001"}).json()))
print("stats:", client.get("/repository/stats").json())

# 4. Dashboard summary.
dash = client.get("/dashboard/summary").json()
print("dashboard keys:", sorted(dash.keys()))
print("total scans:", dash["total_scans"], "| status dist:", dash["status_distribution"])

# 5. Download a generated report file.
import glob
pdf = sorted(glob.glob("data/reports/*.pdf"))
if pdf:
    fn = os.path.basename(pdf[0])
    r = client.get(f"/reports/{fn}")
    print("download report:", r.status_code, "| bytes:", len(r.content))