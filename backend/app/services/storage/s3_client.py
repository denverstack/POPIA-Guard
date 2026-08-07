"""S3-backed report storage.

Reports are uploaded as objects; only the object key is persisted in the
database (see docs/DATABASE.md — presigned URLs expire, so a fresh one is
generated per request rather than storing a URL).
"""

import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Raised for any failure talking to S3 — network, credentials,
    missing bucket, permissions. Callers decide whether that's fatal;
    see scan_service, which treats report storage as best-effort.
    """


class S3StorageService:
    def __init__(self) -> None:
        settings = get_settings()
        self._bucket = settings.s3_bucket_name
        self._client = boto3.client(
            "s3",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )

    def upload_bytes(self, key: str, data: bytes, content_type: str) -> None:
        try:
            self._client.put_object(
                Bucket=self._bucket, Key=key, Body=data, ContentType=content_type
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageError(f"Failed to upload '{key}' to S3: {exc}") from exc

    def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        try:
            return self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=expires_in,
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageError(f"Failed to create a presigned URL for '{key}': {exc}") from exc
