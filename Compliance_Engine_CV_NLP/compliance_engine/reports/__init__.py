"""
Phase 8 - Compliance report generation (PDF + editable formats).

Converts a ComplianceReport (Phases 1-7 output) into:
  * PDF  - human-readable compliance certificate (ReportLab).
  * XLSX - editable evidence table (openpyxl).
  * JSON - machine-readable summary (also what the API returns).

These artifacts are what enforcement officers download / attach to a case.
"""
import json
import os
from typing import Optional

from compliance_engine.reports.base import ENGINE_VERSION, report_to_dict
from compliance_engine.reports.pdf_report import render_pdf
from compliance_engine.reports.xlsx_report import render_xlsx


def export_report(
    report,
    directory: str,
    stem: str = "compliance_report",
    include_json: bool = True,
) -> dict:
    """Export a ComplianceReport to PDF (+ XLSX + JSON) inside `directory`.

    Returns a dict of written file paths.
    """
    os.makedirs(directory, exist_ok=True)
    paths = {}
    pdf_path = os.path.join(directory, f"{stem}.pdf")
    xlsx_path = os.path.join(directory, f"{stem}.xlsx")
    render_pdf(report, pdf_path)
    render_xlsx(report, xlsx_path)
    paths["pdf"] = pdf_path
    paths["xlsx"] = xlsx_path
    if include_json:
        json_path = os.path.join(directory, f"{stem}.json")
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report_to_dict(report), fh, indent=2, default=str)
        paths["json"] = json_path
    return paths


__all__ = [
    "ENGINE_VERSION",
    "render_pdf",
    "render_xlsx",
    "export_report",
    "report_to_dict",
]