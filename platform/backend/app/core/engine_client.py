"""HTTP client for the CV/OCR compliance engine (owned by a teammate module).

The engine is consumed read-only over HTTP - platform code never imports or
modifies the engine package. When the engine is unreachable, callers receive
EngineUnavailable (503) and can fall back to demo imports.
"""
from __future__ import annotations

import json

import httpx

from app.config import get_settings
from app.core.exceptions import EngineUnavailable


class EngineClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.engine_base_url.rstrip("/")
        self.timeout = settings.engine_timeout_seconds

    async def health(self) -> dict | None:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/cv/health")
                if resp.status_code == 200:
                    return resp.json()
        except httpx.HTTPError:
            return None
        return None

    async def compliance_scan(
        self,
        image_bytes: bytes,
        filename: str,
        content_type: str,
        metadata: dict | None = None,
        calibration_mm_per_px: float = 0.0,
    ) -> dict:
        """POST image + metadata to /compliance/scan and return the
        ComplianceReport JSON dict."""
        metadata = metadata or {}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {"file": (filename, image_bytes, content_type)}
                data = {
                    "calibration_mm_per_px": str(calibration_mm_per_px or 0.0),
                    "metadata": json.dumps(metadata),
                }
                resp = await client.post(
                    f"{self.base_url}/compliance/scan", files=files, data=data
                )
        except httpx.HTTPError as exc:
            raise EngineUnavailable(f"{exc.__class__.__name__} while contacting engine") from exc

        if resp.status_code >= 500:
            raise EngineUnavailable(f"engine returned HTTP {resp.status_code}")
        if resp.status_code >= 400:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            raise EngineUnavailable(f"engine rejected scan request: {detail}")

        try:
            report = resp.json()
        except json.JSONDecodeError as exc:  # pragma: no cover
            raise EngineUnavailable("engine returned non-JSON response") from exc

        if report.get("status") == "rejected":
            raise EngineUnavailable(f"engine rejected image: {report.get('message')}")
        return report


engine_client = EngineClient()