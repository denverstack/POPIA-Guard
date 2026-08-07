"""Unit tests for the S3 storage wrapper, run against a mocked S3 backend
(via the autouse mock_s3_bucket fixture in conftest.py) — no real AWS
credentials or network access required or ever attempted.
"""

import json

import boto3
import pytest
from botocore.exceptions import ClientError

from app.core.config import get_settings
from app.services.storage.s3_client import S3StorageService, StorageError


def test_upload_then_retrieve_roundtrips_content() -> None:
    service = S3StorageService()
    payload = json.dumps({"risk_score": 12.0}).encode("utf-8")

    service.upload_bytes("reports/test-user/test-scan.json", payload, "application/json")

    settings = get_settings()
    client = boto3.client("s3", region_name=settings.aws_region)
    stored = client.get_object(
        Bucket=settings.s3_bucket_name, Key="reports/test-user/test-scan.json"
    )
    assert stored["Body"].read() == payload
    assert stored["ContentType"] == "application/json"


def test_presigned_url_points_to_the_right_key() -> None:
    service = S3StorageService()
    service.upload_bytes("reports/u/s.json", b"{}", "application/json")

    url = service.generate_presigned_url("reports/u/s.json", expires_in=120)

    assert url.startswith("http")
    assert "reports/u/s.json" in url


def test_upload_to_nonexistent_bucket_raises_storage_error() -> None:
    service = S3StorageService()
    service._bucket = "a-bucket-that-was-never-created"  # noqa: SLF001

    with pytest.raises(StorageError):
        service.upload_bytes("x.json", b"{}", "application/json")


def test_presigned_url_generation_failure_raises_storage_error(monkeypatch) -> None:
    service = S3StorageService()

    def _boom(*args, **kwargs):
        raise ClientError({"Error": {"Code": "500", "Message": "boom"}}, "GetObject")

    monkeypatch.setattr(service._client, "generate_presigned_url", _boom)  # noqa: SLF001

    with pytest.raises(StorageError):
        service.generate_presigned_url("whatever.json")
