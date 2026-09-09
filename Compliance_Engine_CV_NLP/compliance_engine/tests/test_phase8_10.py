"""Phase 8-10 tests: report generation, repository, dashboard."""
import json
import os

import pytest
from fastapi.testclient import TestClient

from compliance_engine.api import _persist_scan, app
from compliance_engine.dashboard import dashboard_summary
from compliance_engine.pipeline import run_full_pipeline
from compliance_engine.reports import export_report, render_pdf, render_xlsx
from compliance_engine.repository.store import ComplianceRepository


@pytest.fixture(scope="module")
def tmp_repo(tmp_path_factory):
    """Isolated repository for each test run."""
    return ComplianceRepository(str(tmp_path_factory.mktemp("repo")))


@pytest.fixture(scope="module")
def sample_report(sample_images):
    return run_full_pipeline(sample_images[0])


# --- Phase 8: report generation -------------------------------------------
def test_render_pdf_returns_bytes(sample_report):
    data = render_pdf(sample_report)
    assert data and data[:5] == b"%PDF-"


def test_render_pdf_writes_path(tmp_path, sample_report):
    out = str(tmp_path / "r.pdf")
    assert render_pdf(sample_report, out) is None
    assert os.path.exists(out) and os.path.getsize(out) > 1000


def test_render_xlsx_sheets(sample_report):
    data = render_xlsx(sample_report)
    assert data and data[:2] == b"PK"  # xlsx is a zip
    wb = __import__("openpyxl").load_workbook(
        __import__("io").BytesIO(data))
    assert wb.sheetnames == ["Summary", "Declarations", "Violations",
                             "FontMetrics"]


def test_export_report_writes_all(tmp_path, sample_report):
    paths = export_report(sample_report, str(tmp_path), stem="x")
    for key in ("pdf", "xlsx", "json"):
        assert key in paths and os.path.exists(paths[key])


# --- Phase 9: repository ---------------------------------------------------
def test_repository_save_and_get(tmp_repo, sample_report):
    row = tmp_repo.save_scan(sample_report, metadata={"officer": "inspector_a"})
    got = tmp_repo.get_scan(row["scan_id"])
    assert got["meta"]["operator_metadata"]["officer"] == "inspector_a"
    assert got["compliance_status"] == sample_report.compliance_status


def test_repository_list_and_search(tmp_repo, sample_report):
    tmp_repo.save_scan(sample_report, metadata={"officer": "inspector_a"})
    rows = tmp_repo.list_scans()
    assert rows and rows[0]["compliance_status"] == "non_compliant"
    hits = tmp_repo.search(query="inspector_a")
    assert len(hits) >= 1


def test_repository_stats(tmp_repo, sample_report):
    tmp_repo.save_scan(sample_report)
    stats = tmp_repo.stats()
    assert stats["total_scans"] >= 1
    assert stats["status_distribution"].get("non_compliant", 0) >= 1


# --- Phase 10: dashboard ---------------------------------------------------
def test_dashboard_summary_shape(tmp_repo, sample_report):
    tmp_repo.save_scan(sample_report, metadata={"officer": "inspector_b"})
    dash = dashboard_summary(tmp_repo)
    assert dash["total_scans"] >= 1
    assert "status_distribution" in dash
    assert dash["status_distribution"].get("non_compliant", 0) >= 1
    assert "violation_trend" in dash and "officer_activity" in dash
    assert dash["officer_activity"].get("inspector_b", 0) >= 1


# --- API integration --------------------------------------------------------
def test_phase8_10_endpoints(sample_images):
    client = TestClient(app)
    report = run_full_pipeline(sample_images[0])
    row = _persist_scan(report, metadata={"scan_id": "apitest"})
    scan_id = row["scan_id"]

    assert client.get("/repository/scans?limit=10").status_code == 200
    assert client.get(f"/repository/scans/{scan_id}").status_code == 200
    assert client.get("/repository/search", params={"q": "apitest"}).status_code == 200
    assert client.get("/repository/stats").json()["total_scans"] >= 1
    dash = client.get("/dashboard/summary").json()
    assert dash["total_scans"] >= 1

    # report export endpoint (also persists to the repository).
    with open(sample_images[0], "rb") as fh:
        resp = client.post(
            "/compliance/scan/report",
            files={"file": ("p.jpg", fh, "image/jpeg")},
            data={"metadata": json.dumps({"scan_id": "apitest2"})},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert "pdf" in body["files"] and os.path.exists(body["files"]["pdf"])
    assert body["scan_id"] == "apitest2"

    # download the generated PDF.
    pdf_path = body["files"]["pdf"]
    dl = client.get(f"/reports/{os.path.basename(pdf_path)}")
    assert dl.status_code == 200
    assert dl.content[:5] == b"%PDF-"