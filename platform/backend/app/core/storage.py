"""Object-storage abstraction.

Two backends:
  * LocalStorage  - writes under STORAGE_LOCAL_ROOT (default off-line mode)
  * S3Storage     - boto3 against AWS S3 or any S3-compatible endpoint (MinIO)

All platform code depends only on the ``Storage`` protocol, so switching
backends is a configuration change (STORAGE_BACKEND=s3).
"""
from __future__ import annotations

import io
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from app.core.exceptions import StorageError


class Storage(ABC):
    @abstractmethod
    def save(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> dict:
        """Persist bytes under key; returns {key, size_bytes}."""

    @abstractmethod
    def open(self, key: str) -> bytes:
        """Return the full object as bytes."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove the object (idempotent)."""


@dataclass
class LocalStorage(Storage):
    root: Path

    def _resolve(self, key: str) -> Path:
        path = (self.root / key).resolve()
        root_resolved = self.root.resolve()
        if root_resolved not in path.parents and path != root_resolved:
            raise StorageError("storage path traversal blocked")
        return path

    def save(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> dict:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return {"key": key, "size_bytes": len(data)}

    def open(self, key: str) -> bytes:
        path = self._resolve(key)
        if not path.exists():
            raise StorageError(f"object not found: {key}")
        return path.read_bytes()

    def delete(self, key: str) -> None:
        path = self._resolve(key)
        if path.exists():
            path.unlink()


@dataclass
class S3Storage(Storage):
    bucket: str
    client: object  # boto3 client

    def save(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> dict:
        try:
            self.client.put_object(
                Bucket=self.bucket, Key=key, Body=data, ContentType=content_type
            )
        except Exception as exc:  # botocore exceptions are verbose by design
            raise StorageError(f"S3 put failed for {key}: {exc}") from exc
        return {"key": key, "size_bytes": len(data)}

    def open(self, key: str) -> bytes:
        try:
            resp = self.client.get_object(Bucket=self.bucket, Key=key)
            body = resp["Body"]
            data = body.read()
            body.close()
            return data
        except Exception as exc:
            raise StorageError(f"S3 get failed for {key}: {exc}") from exc

    def delete(self, key: str) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
        except Exception as exc:
            raise StorageError(f"S3 delete failed for {key}: {exc}") from exc


_instance: Storage | None = None


def get_storage() -> Storage:
    """Lazily build the configured storage backend (singleton)."""
    global _instance
    if _instance is not None:
        return _instance

    from app.config import get_settings

    settings = get_settings()
    if settings.storage_backend.lower() == "s3":
        try:
            import boto3

            kwargs: dict = {"region_name": settings.s3_region or None}
            if settings.s3_endpoint_url:
                kwargs["endpoint_url"] = settings.s3_endpoint_url
            if settings.aws_access_key_id and settings.aws_secret_access_key:
                kwargs["aws_access_key_id"] = settings.aws_access_key_id
                kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
            client = boto3.client("s3", **{k: v for k, v in kwargs.items() if v})
            # eager connection check so we fall back locally instead of failing at scan time
            client.list_buckets()
            _instance = S3Storage(bucket=settings.s3_bucket, client=client)
        except Exception as exc:  # no S3 credentials / network -> local fallback
            from app.config import PLATFORM_ROOT

            print(f"[storage] S3 unavailable ({exc}); falling back to local")
            _instance = LocalStorage(root=PLATFORM_ROOT / "storage_data")
    else:
        from app.config import PLATFORM_ROOT

        _instance = LocalStorage(root=settings.storage_local_root_path)
    return _instance


def reset_storage_for_tests() -> None:
    global _instance
    _instance = None