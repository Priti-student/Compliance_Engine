"""
Phase 9 - Repository (persistence + retrieval).

A light-weight JSON-file-backed store for scanned products, compliance
reports, and operator metadata. This is the "repository of scanned products
and compliance history" + "search and retrieval facility" requirement.

Why JSON-file-backed: the deliverable must run without external services
(a database server / S3 may not exist in the demo environment). The store
is a small class with an append-only journal + index, and is naturally
replaceable by PostgreSQL/S3 later.

Layout (one directory):
    <dir>/scans/<scan_id>.json      - raw ComplianceReport (full pipeline result)
    <dir>/index.json                - searchable summary rows
"""
import json
import os
import re
import threading
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from compliance_engine.reports.base import report_to_dict


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ComplianceRepository:
    """File-backed store; each method is safe to call concurrently."""

    def __init__(self, directory: str):
        self.directory = os.path.abspath(directory)
        self.scans_dir = os.path.join(self.directory, "scans")
        self.index_path = os.path.join(self.directory, "index.json")
        self._lock = threading.Lock()
        os.makedirs(self.scans_dir, exist_ok=True)
        if not os.path.exists(self.index_path):
            self._write_index([])

    # -- helpers ------------------------------------------------------------
    def _write_index(self, rows: List[dict]) -> None:
        with open(self.index_path, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, indent=2, default=str)

    def _read_index(self) -> List[dict]:
        if not os.path.exists(self.index_path):
            return []
        with open(self.index_path, "r", encoding="utf-8") as fh:
            try:
                return json.load(fh)
            except json.JSONDecodeError:
                return []

    # -- write --------------------------------------------------------------
    def save_scan(
        self,
        report,
        metadata: Optional[dict] = None,
        scan_id: Optional[str] = None,
    ) -> dict:
        """Persist a ComplianceReport + optional metadata; returns the row."""
        scan_id = scan_id or uuid.uuid4().hex[:12]
        created = _now_iso()
        filename = f"{scan_id}.json"
        payload = report_to_dict(report)
        payload["meta"] = {"scan_id": scan_id, "created": created,
                           "operator_metadata": metadata or {}}
        with open(os.path.join(self.scans_dir, filename), "w",
                  encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, default=str)

        row = {
            "scan_id": scan_id,
            "created": created,
            "compliance_status": report.compliance_status,
            "missing": report.stats.missing if report.stats else 0,
            "non_compliant": report.stats.non_compliant if report.stats else 0,
            "needs_review": report.stats.needs_review if report.stats else 0,
            "filename": filename,
            "metadata": metadata or {},
        }
        with self._lock:
            index = self._read_index()
            index = [r for r in index if r["scan_id"] != scan_id]  # idempotent
            index.append(row)
            self._write_index(index)
        return row

    # -- read ---------------------------------------------------------------
    def get_scan(self, scan_id: str) -> Optional[dict]:
        """Return the stored ComplianceReport dict for a scan_id."""
        path = os.path.join(self.scans_dir, f"{scan_id}.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def list_scans(self, limit: int = 50) -> List[dict]:
        """Return recent scan summary rows (newest first)."""
        rows = self._read_index()
        rows.sort(key=lambda r: r["created"], reverse=True)
        return rows[:limit]

    # -- search -------------------------------------------------------------
    def search(
        self,
        query: str = "",
        compliance_status: Optional[str] = None,
        limit: int = 20,
    ) -> List[dict]:
        """Search the index by free-text (product name, metadata) or status.

        A row matches the free-text query if any of its string fields contains
        the (case-insensitive) substring.
        """
        q = query.strip().lower()
        rows = self.list_scans(limit=1000)
        out = []
        for row in rows:
            if compliance_status and row["compliance_status"] != compliance_status:
                continue
            if q:
                haystack = " ".join(str(v).lower() for v in row.values())
                if q not in haystack:
                    continue
            out.append(row)
            if len(out) >= limit:
                break
        return out

    # -- stats --------------------------------------------------------------
    def stats(self) -> dict:
        """Dashboard-style aggregate over all stored scans."""
        rows = self._read_index()
        total = len(rows)
        by_status: Dict[str, int] = {}
        for r in rows:
            s = r.get("compliance_status") or "unknown"
            by_status[s] = by_status.get(s, 0) + 1
        missing_sum = sum(r.get("missing", 0) for r in rows)
        non_sum = sum(r.get("non_compliant", 0) for r in rows)
        return {
            "total_scans": total,
            "status_distribution": by_status,
            "total_missing_declarations": missing_sum,
            "total_violations": non_sum + missing_sum,
        }