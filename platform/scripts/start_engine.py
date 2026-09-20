"""Start the CV/OCR compliance engine on 127.0.0.1:8000 (detached).

Spawns uvicorn with the engine venv interpreter
(Compliance_Engine_CV_NLP\\venv\\Scripts\\python.exe), waits for /cv/health,
prints the result, and exits — the engine process keeps running independently.

Usage:  platform\\venv\\Scripts\\python.exe scripts\\start_engine.py
        (any python that has httpx; reuse the platform venv)
"""
from __future__ import annotations

import subprocess
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]  # = repo root (Compliance_Engine/)
PY = ROOT / "Compliance_Engine_CV_NLP" / "venv" / "Scripts" / "python.exe"
ENGINE_DIR = ROOT / "Compliance_Engine_CV_NLP"


def main() -> int:
    log = open(ROOT / "engine_server.log", "w", encoding="utf-8")
    err = open(ROOT / "engine_server.err.log", "w", encoding="utf-8")
    proc = subprocess.Popen(
        [
            str(PY),
            "-m",
            "uvicorn",
            "compliance_engine.api:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            ],
        cwd=str(ENGINE_DIR),
        stdout=log,
        stderr=err,
        env={**__import__("os").environ, "TESSDATA_PREFIX": str(ROOT / "tessdata")},
    )
    print("engine pid:", proc.pid)
    with httpx.Client(timeout=10) as c:
        for _ in range(60):
            try:
                r = c.get("http://127.0.0.1:8000/cv/health")
                if r.status_code == 200:
                    print("ENGINE-HEALTH", r.status_code, r.json())
                    return 0
            except httpx.HTTPError:
                pass
            time.sleep(1)
    print("ENGINE-HEALTH TIMEOUT")
    print("--- stderr ---")
    err.flush()
    print((ROOT / "engine_server.err.log").read_text(encoding="utf-8", errors="replace")[-1500:])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())