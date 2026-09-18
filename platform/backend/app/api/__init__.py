"""Router aggregation."""
from fastapi import APIRouter

from app.api import (
    auth,
    dashboard,
    health,
    inspections,
    inspections_media,
    products,
    reports,
    rules,
    search,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(products.router)
api_router.include_router(inspections.router)
api_router.include_router(inspections_media.router)
api_router.include_router(reports.router)
api_router.include_router(search.router)
api_router.include_router(dashboard.router)
api_router.include_router(rules.router)