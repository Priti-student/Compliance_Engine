"""PDF compliance certificate (ReportLab platypus, A4 portrait)."""
from __future__ import annotations

import io
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image as RLImage,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.inspection import Inspection
from app.services.report_meta import report_no

_STATUS_COLOR = {
    "compliant": colors.HexColor("#1a7f37"),
    "non_compliant": colors.HexColor("#d73a49"),
    "needs_review": colors.HexColor("#9a6700"),
    "not_applicable": colors.HexColor("#57606a"),
}


def _footer(canvas_doc, doc):
    canvas_doc.saveState()
    canvas_doc.setFont("Helvetica", 7)
    canvas_doc.setFillColor(colors.grey)
    canvas_doc.drawString(
        18 * mm, 8 * mm,
        "LMPC Compliance Platform · Preliminary screening report · "
        "Enforcement decisions require review of the physical package & evidence.",
    )
    canvas_doc.drawRightString(A4[0] - 18 * mm, 8 * mm, f"Page {doc.page}")
    canvas_doc.restoreState()


def _status_style(status: str):
    return ParagraphStyle(
        "Verdict", fontName="Helvetica-Bold", fontSize=16,
        textColor=_STATUS_COLOR.get(status or "", colors.black),
        alignment=TA_CENTER,
    )


def _h(text, size=11, align=0):
    return ParagraphStyle(f"H{size}", fontName="Helvetica-Bold", fontSize=size,
                          spaceBefore=6, spaceAfter=4, alignment=align)


def _blob(size=8):
    return ParagraphStyle("B", fontName="Helvetica", fontSize=size, leading=size + 1)


def _table(rows, widths, header=True):
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    if header:
        style += [("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                  ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3864")),
                  ("TEXTCOLOR", (0, 0), (-1, 0), colors.white)]
    t.setStyle(TableStyle(style))
    return t


def build_pdf(
    inspection: Inspection,
    annotated_image: bytes | None = None,
    evidence_images: list[bytes] | None = None,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=14 * mm,
        title="Legal Metrology Compliance Report",
        author="LMPC Compliance Platform",
        onPage=_footer,
    )

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    story: list = []

    story.append(Paragraph(
        "GOVERNMENT OF INDIA · LEGAL METROLOGY COMPLIANCE PLATFORM", _h(13, 1)))
    story.append(Paragraph(
        "Legal Metrology (Packaged Commodities) Rules, 2011 — Compliance Report",
        _h(11)))
    story.append(Paragraph(f"Report No. <b>{report_no(inspection)}</b> · generated {now}",
                           _blob()))
    story.append(Spacer(1, 4))

    story.append(Paragraph(
        f"VERDICT: {inspection.compliance_status.upper()}",
        _status_style(inspection.compliance_status)))
    story.append(Spacer(1, 2))

    # --- Inspection metadata ---
    meta_rows = [
        ["Inspection token", inspection.token],
        ["Compliance status", inspection.compliance_status],
        ["Workflow status", inspection.workflow_status],
        ["Product image", inspection.image_name],
        ["Engine scan id", inspection.engine_scan_id or "-"],
        ["Inspecting officer", inspection.officer.full_name if inspection.officer else "-"],
        ["Reviewed by", inspection.reviewer.full_name if inspection.reviewer else "-"],
        ["Remarks", inspection.remarks or "-"],
    ]
    stats = inspection.stats_json or {}
    meta_rows.append(["Total checks / compliant / missing",
                      f"{stats.get('total_checks', 0)} / {stats.get('compliant', 0)} / {stats.get('missing', 0)}"])
    story.append(Paragraph("Inspection metadata", _h(11)))
    story.append(_table(meta_rows, [45 * mm, 140 * mm]))
    story.append(Spacer(1, 6))

    # --- Product ---
    p = inspection.product
    if p:
        story.append(Paragraph("Product", _h(11)))
        prod_rows = [
            ["Generic name", p.generic_name],
            ["Brand / category", f"{p.brand or '-'}  /  {p.category or '-'}"],
            ["Net quantity / MRP", f"{p.net_quantity_text or '-'}  /  {p.mrp or '-'}"],
            ["Manufacturer", p.manufacturer or "-"],
            ["Packer / importer", f"{p.packer or '-'}  /  {p.importer or '-'}"],
            ["Batch no", p.batch_no or "-"],
        ]
        story.append(_table(prod_rows, [45 * mm, 140 * mm]))
        story.append(Spacer(1, 6))

    # --- Annotated image ---
    if annotated_image:
        story.append(Paragraph("Annotated package image (detected declaration zones)", _h(11)))
        story.append(RLImage(io.BytesIO(annotated_image), width=150 * mm,
                             height=150 * mm * 0.7))
        story.append(Spacer(1, 6))

    # --- Declarations ---
    story.append(Paragraph("Extracted declarations", _h(11)))
    decl_rows = [["Field", "Value", "Source zone", "Confidence", "Method"]]
    for d in inspection.declarations:
        decl_rows.append([d.field_name, (d.value or "")[:120], d.source_zone or "-",
                          f"{d.confidence:.2f}", d.method or "-"])
    if len(decl_rows) == 1:
        decl_rows.append(["(none extracted)", "", "", "", ""])
    story.append(_table(decl_rows, [48 * mm, 60 * mm, 30 * mm, 22 * mm, 26 * mm]))
    story.append(Spacer(1, 6))

    # --- Violations ---
    story.append(Paragraph("Violations / review items", _h(11)))
    vio_rows = [["Rule", "Reference", "Status", "Severity", "Reason"]]
    for v in inspection.violations:
        vio_rows.append([v.rule_id, v.rule_reference or "-", v.status, v.severity,
                         v.reason.replace("\n", " ")[:220]])
    if len(vio_rows) == 1:
        vio_rows.append(["(no violations)", "", "", "", ""])
    story.append(_table(vio_rows, [22 * mm, 40 * mm, 30 * mm, 18 * mm, 75 * mm]))
    story.append(Spacer(1, 6))

    # --- Font metrics ---
    story.append(Paragraph("Font metrics / readability", _h(11)))
    font_rows = [["Zone", "Char height (px)", "Height (mm)", "Contrast", "Calibrated"]]
    for m in inspection.font_metrics:
        font_rows.append([m.zone_type, f"{m.char_height_px_median:.1f}",
                          f"{m.char_height_mm_median:.3f}" if m.calibrated else "-",
                          f"{m.contrast_ratio:.2f}", "yes" if m.calibrated else "no"])
    if len(font_rows) == 1:
        font_rows.append(["(no readings)", "", "", "", ""])
    story.append(_table(font_rows, [50 * mm, 34 * mm, 34 * mm, 26 * mm, 20 * mm]))

    # --- Evidence ---
    if evidence_images:
        story.append(PageBreak())
        story.append(Paragraph("Supporting evidence (photographs)", _h(11)))
        for i, img in enumerate(evidence_images, start=1):
            story.append(Paragraph(f"Exhibit {i}", _blob()))
            story.append(RLImage(io.BytesIO(img), width=140 * mm, height=140 * mm * 0.75))
            story.append(Spacer(1, 4))

    # --- Signatures ---
    story.append(Spacer(1, 14))
    sig = Table(
        [["", "", ""],
         ["Enforcement Officer", "Reviewing Authority", "Approved By"]],
        colWidths=[66 * mm, 66 * mm, 66 * mm],
    )
    sig.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.black),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, 1), 9),
        ("TOPPADDING", (0, 0), (-1, 0), 14),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(sig)

    doc.build(story)
    return buffer.getvalue()