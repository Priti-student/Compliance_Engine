"""Dashboard aggregation queries for the enforcement dashboard."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import Date, cast, desc, func
from sqlalchemy.orm import Session

from app.models.inspection import Inspection
from app.models.inspection_details import Violation
from app.models.product import Product

_COMPLIANCE_STATUSES = ("compliant", "non_compliant", "needs_review", "not_applicable")


def summary(db: Session) -> dict:
    total = db.query(func.count(Inspection.id)).scalar() or 0
    by_status = dict(
        db.query(Inspection.compliance_status, func.count(Inspection.id))
        .group_by(Inspection.compliance_status)
        .all()
    )
    total_missing = 0
    total_non = 0
    for insp in db.query(Inspection).all():
        s = insp.stats_json or {}
        total_missing += int(s.get("missing") or 0)
        total_non += int(s.get("non_compliant") or 0)

    products = db.query(func.count(Product.id)).scalar() or 0
    officers = (
        db.query(func.count(func.distinct(Inspection.officer_id))).scalar() or 0
    )
    reviewed = (
        db.query(func.count(Inspection.id))
        .filter(Inspection.workflow_status.in_(["reviewed", "approved"]))
        .scalar()
        or 0
    )
    compliant = int(by_status.get("compliant", 0))
    rate = round(100.0 * compliant / total, 1) if total else 0.0
    avg = round((total_missing + total_non) / total, 2) if total else 0.0
    return {
        "total_inspections": total,
        "status_distribution": {s: int(by_status.get(s, 0)) for s in _COMPLIANCE_STATUSES},
        "total_products": products,
        "active_officers": officers,
        "total_violations": total_missing + total_non,
        "total_missing_declarations": total_missing,
        "reviewed_count": reviewed,
        "compliance_rate_pct": rate,
        "avg_violations_per_scan": avg,
        "last_updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def status_distribution(db: Session) -> list[dict]:
    rows = dict(
        db.query(Inspection.compliance_status, func.count(Inspection.id))
        .group_by(Inspection.compliance_status)
        .all()
    )
    return [{"status": s, "count": int(rows.get(s, 0))} for s in _COMPLIANCE_STATUSES]


def violation_trend(db: Session, days: int = 30) -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).date()

    inspections = (
        db.query(Inspection)
        .filter(cast(Inspection.created_at, Date) >= cast(since, Date))
        .all()
    )
    buckets: dict[str, dict] = {}
    for i in inspections:
        day = i.created_at.strftime("%Y-%m-%d") if i.created_at else ""
        if not day:
            continue
        s = i.stats_json or {}
        b = buckets.setdefault(day, {"date": day, "violations": 0, "missing": 0, "non_compliant": 0})
        b["missing"] += int(s.get("missing") or 0)
        b["non_compliant"] += int(s.get("non_compliant") or 0)
        b["violations"] = b["missing"] + b["non_compliant"]
    return [buckets[d] for d in sorted(buckets)]


def top_violations(db: Session, limit: int = 10) -> list[dict]:
    rows = (
        db.query(
            Violation.rule_id,
            func.max(Violation.rule_reference),
            func.count(Violation.id),
            func.count(func.distinct(Violation.inspection_id)),
        )
        .filter(Violation.status.in_(["missing", "non_compliant"]))
        .group_by(Violation.rule_id)
        .order_by(func.count(Violation.id).desc())
        .limit(limit)
        .all()
    )
    return [
        {"rule_id": rid, "rule_reference": ref or "", "count": cnt, "inspections": insp}
        for rid, ref, cnt, insp in rows
    ]


def officer_activity(db: Session) -> list[dict]:
    """Per-officer scan counts and violation totals (portable, no JSONB SQL)."""
    counts: dict[str, dict] = {}
    for insp in db.query(Inspection).all():
        officer = insp.officer
        key = officer.username if officer else "unknown"
        entry = counts.setdefault(
            key,
            {
                "officer": key,
                "full_name": officer.full_name if officer else "",
                "scans": 0,
                "violations": 0,
            },
        )
        entry["scans"] += 1
        s = insp.stats_json or {}
        entry["violations"] += int(s.get("missing") or 0) + int(s.get("non_compliant") or 0)
    rows = sorted(counts.values(), key=lambda r: r["scans"], reverse=True)
    return rows


def category_stats(db: Session) -> list[dict]:
    rows = (
        db.query(
            func.coalesce(Product.category, "uncategorised"),
            func.count(Inspection.id),
        )
        .join(Product, Inspection.product_id == Product.id)
        .group_by(Product.category)
        .order_by(func.count(Inspection.id).desc())
        .all()
    )
    return [{"category": cat, "scans": int(n)} for cat, n in rows]


def recent(db: Session, limit: int = 10) -> list[dict]:
    rows = (
        db.query(Inspection)
        .order_by(desc(Inspection.created_at))
        .limit(limit)
        .all()
    )
    return [r.summary() for r in rows]