"""Smoke-check a Python environment: version + key packages."""
import sys

print("PYTHON", sys.version.split()[0])

mods = ["fastapi", "sqlalchemy", "reportlab", "openpyxl", "httpx", "boto3", "PIL", "pytest", "jwt"]
missing = []
for m in mods:
    try:
        __import__(m)
    except Exception as exc:  # noqa: BLE001
        missing.append(f"{m}: {exc}")
if missing:
    print("MISSING:", "; ".join(missing))
    raise SystemExit(1)
print("PKGS-OK")