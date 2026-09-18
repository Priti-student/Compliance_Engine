"""Report artifact generation + persistence (PDF / XLSX / JSON)."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequest, NotFound, StorageError
from app.core.storage import Storage
from app.models.inspection import Inspection
from app.models.report_evidence import ReportArtifact
from app.services.annotation import annotate_image
from app.services.pdf_builder import build_pdf
from app.services.report_meta import report_filename, report_no
from app.services.xlsx_builder import build_xlsx

_TYPES = ("pdf", "xlsx", "json")


def _now_utc_str() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_json_bytes(inspection: Inspection, generated_by: str | None = None) -> bytes:
    """JSON artifact: platform meta + the untouched engine ComplianceReport."""
    payload = {
        "meta": {
            "report_no": report_no(inspection),
            "token": inspection.token,
            "generated_at": _now_utc_str(),
            "generated_by": generated_by,
            "platform": "LMPC Compliance Platform",
        },
        "compliance_report": inspection.compliance_json,
    }
    return json.dumps(payload, indent=2, default=str).encode("utf-8")


def _collect_images(storage: Storage, inspection: Inspection):
    annotated: bytes | None = None
    if inspection.image_key:
        try:
            raw = storage.open(inspection.image_key)
            zones = (inspection.compliance_json or {}).get("scan", {}).get("zones", [])
            annotated = annotate_image(raw, zones or [])
        except StorageError:
            annotated = None
    evidence: list[bytes] = []
    for e in inspection.evidence:
        try:
            evidence.append(storage.open(e.storage_key))
        except StorageError:
            continue
    return annotated, evidence


def _render(report_type: str, inspection: Inspection, storage: Storage) -> bytes:
    if report_type == "json":
        return build_json_bytes(inspection, generated_by=f"user:{inspection.officer_id}")
    annotated, evidence = _collect_images(storage, inspection)
    if report_type == "pdf":
        return build_pdf(inspection, annotated_image=annotated, evidence_images=evidence or None)
    if report_type == "xlsx":
        return build_xlsx(inspection)
    raise BadRequest(f"unknown report type: {report_type}")


def generate_artifact(
    db: Session,
    inspection: Inspection,
    user,
    storage: Storage,
    report_type: str,
) -> ReportArtifact:
    """Render one artifact, persist it, and upsert its DB row."""
    if report_type not in _TYPES:
        raise BadRequest(f"report_type must be one of {_TYPES}")
    data = _render(report_type, inspection, storage)
    ext = "xlsx" if report_type == "xlsx" else report_type
    filename = report_filename(inspection, ext)
    key = f"inspections/{inspection.token}/reports/{filename}"
    storage.save(key, data, _MIME[report_type])

    db.query(ReportArtifact).filter(
        ReportArtifact.inspection_id == inspection.id,
        ReportArtifact.report_type == report_type,
    ).delete()
    db.flush()
    art = ReportArtifact(
        inspection_id=inspection.id,
        report_type=report_type,
        storage_key=key,
        filename=filename,
        size_bytes=len(data),
        created_by=user.id,
        created_at=_now_utc_str(),
    )
    db.add(art)
    db.commit()
    db.refresh(art)
    return art


def generate_all(db: Session, inspection: Inspection, user, storage: Storage) -> list[ReportArtifact]:
    return [generate_artifact(db, inspection, user, storage, t) for t in _TYPES]


def get_artifact(db: Session, inspection: Inspection, report_type: str) -> ReportArtifact:
    return (
        db.query(ReportArtifact)
        .filter(
            ReportArtifact.inspection_id == inspection.id,
            ReportArtifact.report_type == report_type,
        )
        .first()
    )


def get_artifact_or_404(db: Session, inspection: Inspection, report_type: str) -> ReportArtifact:
    art = get_artifact(db, inspection, report_type)
    if art is None:
        raise NotFound(f"No {report_type} artifact generated yet for {inspection.token}")
    return art


_MIME = {
    "pdf": "application/pdf",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "json": "application/json",
}