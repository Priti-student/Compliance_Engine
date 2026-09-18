"""Database bootstrap: create tables, seed users, import demo inspections."""
from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models.user import ROLE_ADMIN, ROLE_REVIEWER, ROLE_OFFICER, User
from app.services.demo_import import import_demo_report

log = logging.getLogger("seed")

DEMO_USERS = [
    {"username": "admin", "full_name": "Admin One", "email": "admin@lmpc.gov.in",
     "password": "Admin@123", "role": ROLE_ADMIN},
    {"username": "reviewer", "full_name": "Ravi Kumar", "email": "reviewer@lmpc.gov.in",
     "password": "Reviewer@123", "role": ROLE_REVIEWER},
    {"username": "officer", "full_name": "Priya Sharma", "email": "officer@lmpc.gov.in",
     "password": "Officer@123", "role": ROLE_OFFICER},
]


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


def seed_users(db: Session) -> list[User]:
    users = []
    for u in DEMO_USERS:
        user = db.query(User).filter(User.username == u["username"]).first()
        if user is None:
            user = User(
                username=u["username"],
                full_name=u["full_name"],
                email=u["email"],
                password_hash=hash_password(u["password"]),
                role=u["role"],
            )
            db.add(user)
        else:
            user.role = u["role"]
            user.is_active = True
        users.append(user)
    db.commit()
    return users


def seed_demo_inspections(db: Session, storage, force: bool = False) -> int:
    """Import every *.json under DEMO_IMPORT_DIR as an inspection."""
    settings = get_settings()
    demo_dir = settings.demo_import_dir_abs
    if not demo_dir.is_dir():
        log.warning("demo import dir not found: %s", demo_dir)
        return 0

    images_dir = settings.demo_engine_root

    if not force:
        from app.models.inspection import Inspection

        existing = db.query(Inspection.id).first()
        if existing:
            log.info("inspections table not empty; skipping demo import (force to override)")
            return 0

    officer = db.query(User).filter(User.username == "officer").first()
    if officer is None:
        officer = seed_users(db)[2]

    imported = 0
    from app.services import report_service

    for src in sorted(demo_dir.glob("*.json")):
        try:
            inspection = import_demo_report(
                db, officer, storage, src.name, demo_dir, images_dir
            )
            report_service.generate_all(db, inspection, officer, storage)
            imported += 1
        except Exception as exc:  # keep boot resilient to one bad file
            log.warning("failed to import %s: %s", src.name, exc)
    return imported


def run_seed(force_demo: bool = False) -> None:
    create_tables()
    db = SessionLocal()
    try:
        users = seed_users(db)
        log.info("seeded %d users", len(users))
        settings = get_settings()
        from app.core.storage import get_storage

        n = seed_demo_inspections(
            db, get_storage(), force=force_demo or settings.seed_demo.lower() == "force"
        )
        log.info("imported %d demo inspections", n)
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_seed()