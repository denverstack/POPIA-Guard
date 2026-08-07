"""Shared test fixtures.

Each test gets a fresh in-memory SQLite database (tables created and
dropped per test) via a FastAPI dependency override, so tests never share
state or depend on a running Postgres instance.
"""

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app

_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@pytest.fixture(autouse=True)
def mock_s3_bucket():
    """Every test runs inside a mocked AWS environment — no test ever
    attempts a real network call to S3. Pre-creates the configured
    bucket so scan_service's report upload has somewhere to write to.
    """
    with mock_aws():
        settings = get_settings()
        client = boto3.client("s3", region_name=settings.aws_region)
        if settings.aws_region == "us-east-1":
            client.create_bucket(Bucket=settings.s3_bucket_name)
        else:
            client.create_bucket(
                Bucket=settings.s3_bucket_name,
                CreateBucketConfiguration={"LocationConstraint": settings.aws_region},
            )
        yield


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=_engine)
    session = _TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=_engine)


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    """Registers and logs in a user, returning ready-to-use auth headers."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "jane@example.com",
            "password": "correct-horse-battery",
            "full_name": "Jane Doe",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "jane@example.com", "password": "correct-horse-battery"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
