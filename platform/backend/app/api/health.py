"""Health endpoints."""
from fastapi import APIRouter, Depends

from app.core.engine_client import engine_client
from app.database import engine

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    db_ok = True
    try:
        with engine.connect():
            pass
    except Exception:
        db_ok = False
    engine_health = await engine_client.health()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "ok" if db_ok else "unreachable",
        "engine_online": engine_health is not None,
        "engine": engine_health,
    }