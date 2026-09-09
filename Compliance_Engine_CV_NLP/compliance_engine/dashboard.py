"""
Phase 10 - Dashboard aggregation.

Turns the repository contents into the numbers a monitoring dashboard shows:
  - compliance status distribution (pie)
  - violation trend over time (bar/line)
  - officer-wise activity (per-operator scan counts)
  - recent scans list
  - top violation types

Pure functions over ComplianceRepository -- no UI-specific types, so any
frontend (Recharts / Chart.js on the React dashboard) can consume the JSON
directly.
"""
from collections import Counter
from typing import Dict, List

from compliance_engine.repository.store import ComplianceRepository


def dashboard_summary(repo: ComplianceRepository, days: int = 30) -> dict:
    """Aggregate metrics for the enforcement-officer dashboard."""
    scans = repo.list_scans(limit=100000)

    status_dist: Dict[str, int] = Counter(r["compliance_status"] for r in scans)

    # Violation trend (last `days`).
    trend: Dict[str, int] = Counter()
    for r in scans:
        day = (r.get("created") or "")[:10]
        if day:
            trend[day] += r.get("missing", 0) + r.get("non_compliant", 0)

    # Officer-wise activity (from metadata.operator / officer if provided).
    officer: Dict[str, int] = Counter()
    for r in scans:
        op = r.get("metadata", {}).get("officer") or "unknown"
        officer[op] += 1

    # Top violation rule types (from the stored full reports).
    rule_counter: Counter = Counter()
    for r in scans:
        sid = r["scan_id"]
        report = repo.get_scan(sid)
        if not report:
            continue
        for v in report.get("violations", []):
            if v.get("status") in ("missing", "non_compliant"):
                rule_counter[v.get("rule_id", "?")] += 1

    return {
        "total_scans": len(scans),
        "status_distribution": dict(status_dist),
        "violation_trend": dict(sorted(trend.items())),
        "officer_activity": dict(officer),
        "top_violation_rules": rule_counter.most_common(10),
        "recent_scans": scans[:10],
    }