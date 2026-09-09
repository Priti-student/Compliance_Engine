"""
Phase 8 - PDF compliance certificate (ReportLab).
"""
from io import BytesIO
from typing import Union

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from compliance_engine.reports.base import ENGINE_VERSION, _now_iso, _calibration_text
from compliance_engine.schema import ComplianceReport

_STATUS_COLOR = {
    "compliant": colors.HexColor("#1a7f37"),
    "non_compliant": colors.HexColor("#d73a49"),
    "needs_review": colors.HexColor("#9a6700"),
    "not_applicable": colors.HexColor("#57606a"),
}


def _verdict_style(status: str):
    return ParagraphStyle(
        "Verdict", fontName="Helvetica-Bold", fontSize=18,
        textColor=_STATUS_COLOR.get(status or "", colors.black),
    )


def _meta_rows(report: ComplianceReport):
    scan = report.scan
    img = f"{scan.image_width}x{scan.image_height}px" if scan else "-"
    cal = report.calibration
    return [
        ["Product image", img],
        ["Calibration", _calibration_text(report)],
        ["Barcode value", cal.barcode_value if cal else ""],
        ["Total checks", str(report.stats.total_checks if report.stats else 0)],
        ["Generated (UTC)", _now_iso()],
    ]


def render_pdf(
    report: ComplianceReport,
    out: Union[str, BytesIO, None] = None,
) -> Union[bytes, None]:
    """Render the compliance report as a PDF.

    out=None -> returns bytes; out=str -> writes to path;
    out=BytesIO -> writes to buffer (returns None).
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=14 * mm,
        title="Legal Metrology Compliance Report",
        author="LMPC Compliance Engine",
    )

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12,
                        spaceBefore=8, spaceAfter=4)
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=9)

    story = []
    story.append(Paragraph(
        "Legal Metrology (Packaged Commodities) Rules, 2011 — Compliance Report",
        h1,
    ))
    story.append(Paragraph(
        f"Engine v{ENGINE_VERSION} · generated {_now_iso()}", body,
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"VERDICT: {report.compliance_status.upper()}",
        _verdict_style(report.compliance_status),
    ))

    meta = Table(_meta_rows(report), colWidths=[55 * mm, 95 * mm])
    meta.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(Spacer(1, 4))
    story.append(meta)

    # Declarations.
    story.append(Paragraph("Extracted declarations", h2))
    decl_rows = [["Field", "Value", "Source", "Conf."]]
    for d in report.declarations:
        decl_rows.append([d.field_name, d.value or "-", d.source_zone,
                          f"{d.confidence:.2f}"])
    if not report.declarations:
        decl_rows.append(["(none extracted)", "", "", ""])
    dt = Table(decl_rows, colWidths=[48 * mm, 52 * mm, 28 * mm, 18 * mm])
    dt.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(dt)

    # Violations.
    story.append(Paragraph("Violations / review items", h2))
    vio_rows = [["Rule", "Status", "Severity", "Reason"]]
    for v in report.violations:
        vio_rows.append([v.rule_id, v.status, v.severity,
                         v.reason.replace("\n", " ")[:120]])
    if not report.violations:
        vio_rows.append(["(no violations)", "", "", ""])
    vt = Table(vio_rows, colWidths=[16 * mm, 28 * mm, 16 * mm, 90 * mm])
    vt.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(vt)

    # Font metrics.
    story.append(Paragraph("Font metrics (readability)", h2))
    font_rows = [["Zone", "Char height (px)", "Height (mm)", "Contrast"]]
    for m in report.font_metrics:
        font_rows.append([
            m.zone_type,
            f"{m.char_height_px_median:.1f}",
            f"{m.char_height_mm_median:.3f}" if m.calibrated else "-",
            f"{m.contrast_ratio:.2f}",
        ])
    ft = Table(font_rows, colWidths=[45 * mm, 35 * mm, 35 * mm, 25 * mm])
    ft.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
    ]))
    story.append(ft)

    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Generated by the LMPC Compliance Engine. This report is for "
        "preliminary screening; enforcement decisions require review of the "
        "physical package and the underlying evidence images.",
        body,
    ))

    doc.build(story)
    data = buffer.getvalue()

    if out is None:
        return data
    if isinstance(out, str):
        with open(out, "wb") as fh:
            fh.write(data)
        return None
    out.write(data)
    return None