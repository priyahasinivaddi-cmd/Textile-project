"""Pluggable image storage with local-development and S3-compatible providers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.config import settings


class StorageProvider(ABC):
    @abstractmethod
    def save(self, key: str, payload: bytes, content_type: str) -> str: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...


class LocalStorageProvider(StorageProvider):
    def __init__(self, root: str = settings.upload_dir):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, key: str, payload: bytes, content_type: str) -> str:
        path = self.root / Path(key).name
        path.write_bytes(payload)
        return f"/static/uploads/{path.name}"

    def delete(self, key: str) -> None:
        path = self.root / Path(key).name
        if path.exists():
            path.unlink()


class S3StorageProvider(StorageProvider):
    def __init__(self):
        if not settings.s3_bucket:
            raise RuntimeError("S3_BUCKET is required when STORAGE_BACKEND=s3")
        import boto3
        self.bucket = settings.s3_bucket
        self.client = boto3.client("s3", endpoint_url=settings.s3_endpoint_url, region_name=settings.s3_region)

    def save(self, key: str, payload: bytes, content_type: str) -> str:
        object_key = f"garments/{Path(key).name}"
        self.client.put_object(Bucket=self.bucket, Key=object_key, Body=payload, ContentType=content_type)
        return f"s3://{self.bucket}/{object_key}"

    def delete(self, key: str) -> None:
        object_key = key.split(f"s3://{self.bucket}/", 1)[-1]
        self.client.delete_object(Bucket=self.bucket, Key=object_key)


storage_provider: StorageProvider = S3StorageProvider() if settings.storage_backend == "s3" else LocalStorageProvider()
