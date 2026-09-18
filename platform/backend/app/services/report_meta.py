"""Shared report numbering / filenames."""
from app.models.inspection import Inspection


def report_no(inspection: Inspection) -> str:
    ts = (
        inspection.created_at.strftime("%Y%m%d")
        if hasattr(inspection.created_at, "strftime") and inspection.created_at
        else "00000000"
    )
    return f"LMPC-{ts}-{inspection.token[:6].upper()}"


def report_filename(inspection: Inspection, extension: str) -> str:
    return f"{report_no(inspection)}.{extension}"