"""Application configuration (environment driven via .env at platform root)."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# platform/backend/app/config.py -> platform root is three levels up.
PLATFORM_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PLATFORM_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application ---
    app_name: str = "LMPC Compliance Platform"
    api_prefix: str = "/api"
    debug: bool = True

    # --- Database ---
    database_url: str = (
        "postgresql+psycopg://postgres:Subhanshu$175@localhost:5432/lmpc_platform"
    )
    # sqlite:// keeps unit tests self-contained; production uses PostgreSQL.
    test_database_url: str = "sqlite://"

    # --- Auth / JWT ---
    jwt_secret: str = "dev-secret-change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60

    # --- CV/OCR engine (owned by teammate; consumed over HTTP, never modified) ---
    engine_base_url: str = "http://127.0.0.1:8000"
    engine_timeout_seconds: float = 60.0

    # --- Object storage (local | s3); s3 falls back to local on connection error ---
    storage_backend: str = "local"
    storage_local_root: str = "./storage_data"
    s3_bucket: str = "lmpc-platform"
    s3_region: str = "ap-south-1"
    s3_endpoint_url: str = ""
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # --- Demo / seed ---
    demo_import_dir: Path = (
        PLATFORM_ROOT.parent
        / "Compliance_Engine_CV_NLP"
        / "data"
        / "demo"
        / "reports"
    )
    seed_demo: str = "true"  # true | false | force

    # --- CORS ---
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- Limits ---
    max_upload_mb: int = 15

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def storage_local_root_path(self) -> Path:
        p = Path(self.storage_local_root)
        return p if p.is_absolute() else (PLATFORM_ROOT / p)

    @property
    def demo_import_dir_abs(self) -> Path:
        """DEMO_IMPORT_DIR resolved against the platform root when relative."""
        p = Path(self.demo_import_dir)
        return (p if p.is_absolute() else (PLATFORM_ROOT / p)).resolve()

    @property
    def demo_engine_root(self) -> Path:
        """Compliance_Engine_CV_NLP folder (holds the demo sample images)."""
        return self.demo_import_dir_abs.parents[2]


@lru_cache
def get_settings() -> Settings:
    return Settings()