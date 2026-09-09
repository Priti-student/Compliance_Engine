"""
FastAPI endpoint exposing the Phases 1-10 compliance engine.

    GET  /cv/health                  -> Tesseract/OpenCV availability
    POST /cv/scan                    -> Phases 1-4 CV-only ScanResult
    POST /compliance/scan            -> Phases 1-7 ComplianceReport
    POST /compliance/scan/report     -> Phases 1-8: run scan + write PDF/XLSX/JSON
    GET  /repository/scans           -> repository index (latest first)
    GET  /repository/scans/{id}      -> one stored report
    GET  /repository/search          -> search repository
    GET  /repository/stats           -> aggregate counts
    GET  /dashboard/summary          -> dashboard aggregates

The /repository + /dashboard routes build a scan repository and monitoring
dashboard (Phases 9-10). Reports/ are written into ./data/reports by default.

For quick local development:

    uvicorn compliance_engine.api:app --reload
"""
import json
import os
from typing import Dict, List, Optional

import cv2
import pytesseract
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from compliance_engine import config
from compliance_engine.dashboard import dashboard_summary
from compliance_engine.pipeline import run_full_pipeline, run_scan
from compliance_engine.reports import export_report
from compliance_engine.repository.store import ComplianceRepository
from compliance_engine.schema import ComplianceReport, ScanResult

# Repository / report storage (created lazily).
_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
_REPO_DIR = os.path.join(_DATA_DIR, "repository")
_REPORTS_DIR = os.path.join(_DATA_DIR, "reports")

repository = ComplianceRepository(_REPO_DIR)

app = FastAPI(
    title="LMPC Compliance Engine - CV/OCR Service",
    description="Image quality gate, preprocessing, declaration-zone detection, "
                "OCR extraction, NLP declaration extraction, rule-engine "
                "compliance, report generation, repository and dashboard for "
                "Legal Metrology (Packaged Commodities) Rules, 2011.",
    version="0.2.0",
)


@app.get("/cv/health", summary="Service health and dependency versions")
def health() -> Dict[str, str]:
    tess_version = pytesseract.get_tesseract_version()
    return {
        "status": "ok",
        "opencv_version": cv2.__version__,
        "tesseract_version": str(tess_version),
        "tesseract_path": config.TESSERACT_CMD,
    }


@app.post("/cv/scan", response_model=ScanResult, summary="Scan one product image")
async def scan_image(file: UploadFile = File(...)) -> ScanResult:
    """Run Phases 1-4 on an uploaded product/label image."""
    content_type = (file.content_type or "").lower()
    if not content_type.startswith("image/"):
        raise HTTPException(
            status_code=415,
            detail="Upload must be an image (content-type image/*).",
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty upload.")

    result = run_scan(data)
    if result.status == "rejected":
        raise HTTPException(status_code=422, detail=result.message)
    return result


@app.post(
    "/compliance/scan",
    response_model=ComplianceReport,
    summary="Full compliance scan (Phases 1-7)",
)
async def compliance_scan(
    file: UploadFile = File(...),
    calibration_mm_per_px: float = Form(0.0),
    metadata: str = Form(""),
) -> ComplianceReport:
    """Run the full pipeline: image -> OCR -> declarations -> rule engine.

    - calibration_mm_per_px: optional manual pixel-to-mm conversion (0 = auto
      via in-image barcode, when present).
    - metadata: optional JSON string for condition latches
      (e.g. {"package_flagged_as_imported": true}, {"product_category": "textiles"}).
    """
    content_type = (file.content_type or "").lower()
    if not content_type.startswith("image/"):
        raise HTTPException(
            status_code=415,
            detail="Upload must be an image (content-type image/*).",
        )
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty upload.")

    parsed_metadata = {}
    if metadata.strip():
        import json
        try:
            parsed_metadata = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400, detail="metadata must be a valid JSON object.",
            )

    report = run_full_pipeline(
        data,
        metadata=parsed_metadata,
        calibration_mm_per_px=calibration_mm_per_px or None,
    )
    if report.status == "rejected":
        raise HTTPException(status_code=422, detail=report.message)
    return report


# ---------------------------------------------------------------------------
# Phase 8 - report generation endpoints
# ---------------------------------------------------------------------------
@app.post("/compliance/scan/report", summary="Run scan and export PDF/XLSX/JSON")
async def compliance_scan_report(
    file: UploadFile = File(...),
    calibration_mm_per_px: float = Form(0.0),
    metadata: str = Form(""),
) -> dict:
    """Run the full pipeline and write PDF + XLSX (+ JSON) into ./data/reports.

    Returns the file paths so the backend can serve/attach them.
    """
    content_type = (file.content_type or "").lower()
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=415,
                            detail="Upload must be an image (image/*).")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty upload.")

    parsed_metadata = {}
    if metadata.strip():
        try:
            parsed_metadata = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400,
                                detail="metadata must be a valid JSON object.")

    report = run_full_pipeline(data, metadata=parsed_metadata,
                               calibration_mm_per_px=calibration_mm_per_px or None)
    if report.status == "rejected":
        raise HTTPException(status_code=422, detail=report.message)

    stem = f"scan_{parsed_metadata.get('scan_id', 'report')}"
    paths = export_report(report, _REPORTS_DIR, stem=stem)
    # Persist to the repository automatically (scan history).
    _persist_scan(report, parsed_metadata)
    return {"compliance_status": report.compliance_status,
            "scan_id": parsed_metadata.get("scan_id", ""),
            "advice": report.advice, "files": paths}


@app.get("/reports/{filename}", summary="Download a generated report file")
def get_report_file(filename: str):
    """Serve a generated PDF/XLSX/JSON report (basic path safety)."""
    safe = os.path.basename(filename)
    path = os.path.join(_REPORTS_DIR, safe)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Report not found.")
    return FileResponse(path, filename=safe)


# ---------------------------------------------------------------------------
# Phase 9 - repository endpoints
# ---------------------------------------------------------------------------
@app.get("/repository/scans", summary="List recent scans")
def list_scans(limit: int = Query(20, ge=1, le=100)):
    return repository.list_scans(limit=limit)


@app.get("/repository/scans/{scan_id}", summary="Get one stored scan")
def get_scan(scan_id: str):
    row = repository.get_scan(scan_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Scan not found.")
    return row


@app.get("/repository/search", summary="Search the repository")
def search_scans(
    q: str = "",
    status: Optional[str] = Query(None, alias="compliance_status"),
    limit: int = Query(20, ge=1, le=100),
) -> List[dict]:
    return repository.search(query=q, compliance_status=status, limit=limit)


@app.get("/repository/stats", summary="Aggregate repository counts")
def repository_stats() -> dict:
    return repository.stats()


# ---------------------------------------------------------------------------
# Phase 10 - dashboard aggregation endpoint
# ---------------------------------------------------------------------------
@app.get("/dashboard/summary", summary="Dashboard aggregate metrics")
def dashboard() -> dict:
    return dashboard_summary(repository)


# Saves a completed ComplianceReport for the repository (used by the
# report-flow above and external integrations; GUs call this after a scan).
def _persist_scan(report: ComplianceReport, metadata: dict) -> dict:
    return repository.save_scan(report, metadata=metadata)