"""
Phase 8 - Report generation (PDF via ReportLab + XLSX via openpyxl).

All exporters are pure functions: (ComplianceReport, out) -> artefact. They
never re-run the pipeline, so report generation is cheap and repeatable.

PDF  = compliance certificate (verdict banner, declarations, violations, font).
XLSX = editable workbook (Summary / Declarations / Violations / FontMetrics).
JSON = machine-readable summary (same as what the API returns).
"""
import os
from datetime import datetime, timezone

from compliance_engine.schema import ComplianceReport

ENGINE_VERSION = "0.2.0"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _calibration_text(report: ComplianceReport) -> str:
    cal = report.calibration
    if not cal or not cal.method:
        return "none"
    return f"{cal.method} ({cal.mm_per_px:.5f} mm/px)"


def report_to_dict(report: ComplianceReport) -> dict:
    """Serialize a ComplianceReport to a JSON-safe dict."""
    import dataclasses

    def _d(value):
        if dataclasses.is_dataclass(value):
            return {k: _d(v) for k, v in dataclasses.asdict(value).items()}
        if isinstance(value, (list, tuple)):
            return [_d(v) for v in value]
        if isinstance(value, dict):
            return {k: _d(v) for k, v in value.items()}
        return value

    return _d(report)