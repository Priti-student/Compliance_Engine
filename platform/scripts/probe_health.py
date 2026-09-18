"""Probe the platform backend health endpoint."""
import httpx

r = httpx.get("http://127.0.0.1:8001/api/health", timeout=10)
print("HEALTH", r.status_code, r.json())