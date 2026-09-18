"""DB bootstrap sanity checks (no internet / interactivity needed)."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.main import app  # noqa: E402
from app.config import get_settings  # noqa: E402

s = get_settings()
print("APP-IMPORT-OK routes=", len(app.routes))
for r in app.routes:
    methods = ",".join(sorted(getattr(r, "methods", []) or []))
    print(" ", methods, getattr(r, "path", repr(r)))
print("DB url host:", s.database_url.split("@")[1].split("/")[0])
print("storage backend:", s.storage_backend)
print("demo abs dir:", s.demo_import_dir_abs)
print("demo engine root:", s.demo_engine_root)
print("engine base url:", s.engine_base_url)