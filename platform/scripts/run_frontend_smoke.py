"""Boot backend + vite dev server, probe proxy & SPA routes, then stop both.

Usage: platform\\venv\\Scripts\\python.exe platform\\scripts\\run_frontend_smoke.py
Requires: npm install already run in platform/frontend, seeded DB.
"""
from __future__ import annotations

import subprocess
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / "venv" / "Scripts" / "python.exe"
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
PROCS = []


def main() -> int:
    procs = [
        subprocess.Popen(
            [str(PY), "-m", "uvicorn", "app.main:app", "--port", "8001"],
            cwd=str(BACKEND),
            stdout=open(ROOT / "server.log", "w"), stderr=subprocess.STDOUT,
        )
    ]
    procs.append(
        subprocess.Popen(
            ["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"],
            cwd=str(FRONTEND),
            stdout=open(ROOT / "vite.log", "w"), stderr=subprocess.STDOUT,
            shell=True,
        )
    )
    try:
        with httpx.Client(timeout=60) as c:
            # wait for backend
            for _ in range(60):
                try:
                    if c.get("http://127.0.0.1:8001/api/health").status_code == 200:
                        break
                except httpx.HTTPError:
                    time.sleep(1)
            # wait for vite
            for _ in range(60):
                try:
                    if c.get("http://127.0.0.1:5173/").status_code == 200:
                        break
                except httpx.HTTPError:
                    time.sleep(1)

            checks = [
                ("vite-serves-root", "http://127.0.0.1:5173/", 200),
                ("vite-serves-scan", "http://127.0.0.1:5173/scan", 200),
                ("vite-serves-repository", "http://127.0.0.1:5173/repository", 200),
                ("vite-serves-report-route", "http://127.0.0.1:5173/inspections/testtoken", 200),
                ("vite-proxy-health", "http://127.0.0.1:5173/api/health", 200),
            ]
            failed = 0
            for name, url, want in checks:
                try:
                    r = c.get(url)
                    ok = r.status_code == want
                    print(f"[{'ok ' if ok else 'FAIL'}] {name} -> {r.status_code}")
                    if not ok:
                        failed += 1
                except httpx.HTTPError as exc:
                    print(f"[FAIL] {name} -> {exc}")
                    failed += 1

            # API body must come from the proxied backend (JSON), not index.html
            r = c.get("http://127.0.0.1:5173/api/health")
            print(f"[check] proxy returns JSON: {r.headers.get('content-type', '').startswith('application/json')}")
            return 1 if failed else 0
    finally:
        for p in reversed(procs):
            p.terminate()
            try:
                p.wait(timeout=8)
            except subprocess.TimeoutExpired:
                p.kill()


if __name__ == "__main__":
    raise SystemExit(main())