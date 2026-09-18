"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.services.seed import run_seed

    run_seed()  # create tables + seed users + optional demo import
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    description=(
        "Web platform for Legal Metrology (Packaged Commodities) Rules, 2011 "
        "compliance checking: scan products, persist inspections, review, "
        "generate PDF/XLSX/JSON reports, dashboards and repository search."
        " Integrates read-only with the CV/OCR compliance engine."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)