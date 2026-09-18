"""Shared pytest fixtures.

Uses an in-memory SQLite database (models use JSON with a PostgreSQL JSONB
variant, so the same DDL works on SQLite) and a real TestClient. The engine
HTTP client is monkeypatched to return a synthetic ComplianceReport.
"""
from __future__ import annotations

import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_engine, monkeypatch):
    """TestClient with dependency override + demo users pre-seeded.

    Swaps the production storage backend for a throw-away local directory
    and disables the startup seed (no PostgreSQL needed in tests).
    """
    from app.core.security import hash_password
    from app.models.user import (
        ROLE_ADMIN,
        ROLE_OFFICER,
        ROLE_REVIEWER,
        User,
    )

    @asynccontextmanager
    async def _noop_lifespan(_app):
        yield

    app.router.lifespan_context = _noop_lifespan

    Session = sessionmaker(bind=db_engine, autoflush=False, expire_on_commit=False)

    def _override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    from app.core import storage as storage_mod
    from app.core.storage import LocalStorage

    storage_mod._instance = LocalStorage(root=Path(tempfile.mkdtemp(prefix="lmpc_test_")))

    app.dependency_overrides[get_db] = _override

    with TestClient(app) as c:
        db = Session()
        for u in (
            ("admin", "Admin One", "admin@x.in", "Admin@123", ROLE_ADMIN),
            ("reviewer", "Ravi Kumar", "reviewer@x.in", "Reviewer@123", ROLE_REVIEWER),
            ("officer", "Priya Sharma", "officer@x.in", "Officer@123", ROLE_OFFICER),
        ):
            db.add(
                User(
                    username=u[0],
                    full_name=u[1],
                    email=u[2],
                    password_hash=hash_password(u[3]),
                    role=u[4],
                )
            )
        db.commit()
        db.close()
        yield c
        app.dependency_overrides.clear()


def _login(client: TestClient, username: str) -> dict:
    password = {
        "admin": "Admin@123",
        "reviewer": "Reviewer@123",
        "officer": "Officer@123",
    }[username]
    resp = client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.fixture()
def officer_token(client):
    return _login(client, "officer")["access_token"]


@pytest.fixture()
def reviewer_token(client):
    return _login(client, "reviewer")["access_token"]


@pytest.fixture()
def admin_token(client):
    return _login(client, "admin")["access_token"]


def sync_report() -> dict:
    """Synthetic engine ComplianceReport used by tests (engine is mocked)."""
    return {
        "status": "ok",
        "compliance_status": "non_compliant",
        "scan": {
            "status": "ok",
            "image_width": 200,
            "image_height": 300,
            "zones": [
                {"zone_type": "mrp_block", "bbox": [10, 20, 80, 12],
                 "text": "MRP Rs.10.00 (incl. of all taxes)", "confidence": 90.0,
                 "source": "heuristic", "words": []}
            ],
        },
        "calibration": {"method": "none", "mm_per_px": 0.0, "barcode_value": "",
                        "barcode_bbox": [], "reference_width_mm": 0.0,
                        "reference_width_px": 0.0, "notes": ""},
        "font_metrics": [
            {"zone_type": "mrp_block", "char_height_px_median": 12.0,
             "char_height_mm_median": 0.0, "contrast_ratio": 8.4,
             "calibrated": False}
        ],
        "declarations": [
            {"field_name": "generic_name_of_commodity", "value": "Biscuit",
             "raw_text": "Biscuit", "confidence": 0.95, "method": "regex",
             "source_zone": "full_image", "qualifiers": [], "rule_id": "MD-02"},
            {"field_name": "mrp", "value": "MRP Rs.10.00 (incl. of all taxes)",
             "raw_text": "MRP Rs.10.00", "confidence": 0.9, "method": "regex",
             "source_zone": "mrp_block", "qualifiers": [], "rule_id": "MD-05"},
        ],
        "violations": [
            {"rule_id": "MD-04", "rule_reference": "Rule 6(1)(d)",
             "field_name": "month_year_of_manufacture", "status": "missing",
             "severity": "high", "reason": "Month and year of manufacture not declared",
             "evidence": {}}
        ],
        "stats": {"total_checks": 12, "compliant": 8, "non_compliant": 1,
                  "missing": 2, "needs_review": 1, "not_applicable": 0},
        "warnings": [], "advice": ["re-capture recommended"],
    }


@pytest.fixture()
def mock_engine(monkeypatch):
    """Stub the engine HTTP client to return the synthetic report."""

    async def fake_scan(*args, **kwargs):
        return sync_report()

    async def fake_health():
        return {"status": "ok", "opencv_version": "4.x", "tesseract_version": "5.x"}

    from app.core import engine_client as ec

    monkeypatch.setattr(ec.engine_client, "compliance_scan", fake_scan)
    monkeypatch.setattr(ec.engine_client, "health", fake_health)
    return ec.engine_client