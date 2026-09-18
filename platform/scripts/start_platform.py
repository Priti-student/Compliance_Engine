"""Start the platform backend on 127.0.0.1:8001 (detached).

Spawns the uvicorn launcher (backend/run.py), waits for /api/health, prints
the result, and exits — the backend process keeps running independently.
"""
from __future__ import annotations

import subprocess
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]  # platform/
PY = ROOT / "venv" / "Scripts" / "python.exe"
BACKEND = ROOT / "backend"


def main() -> int:
    log = open(ROOT / "server.log", "w", encoding="utf-8")
    err = open(ROOT / "server.err.log", "w", encoding="utf-8")
    proc = subprocess.Popen(
        [str(PY), "run.py"],
        cwd=str(BACKEND),
        stdout=log,
        stderr=err,
    )
    print("platform pid:", proc.pid)
    with httpx.Client(timeout=10) as c:
        for _ in range(60):
            try:
                r = c.get("http://127.0.0.1:8001/api/health")
                if r.status_code == 200:
                    print("PLATFORM-HEALTH", r.json())
                    return 0
            except httpx.HTTPError:
                pass
            time.sleep(1)
    print("PLATFORM-HEALTH TIMEOUT")
    print("--- stderr ---")
    err.flush()
    print((ROOT / "server.err.log").read_text(encoding="utf-8", errors="replace")[-1500:])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())