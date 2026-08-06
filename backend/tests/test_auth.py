"""Integration tests for register/login and protected-route access."""

from fastapi.testclient import TestClient


def test_register_creates_user(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@example.com",
            "password": "correct-horse-battery",
            "full_name": "New User",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert "hashed_password" not in body  # never leak the hash


def test_register_duplicate_email_rejected(client: TestClient) -> None:
    payload = {"email": "dup@example.com", "password": "correct-horse-battery", "full_name": "Dup"}
    first = client.post("/api/v1/auth/register", json=payload)
    second = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201
    assert second.status_code == 409


def test_login_with_correct_credentials_returns_token(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "ok@example.com", "password": "correct-horse-battery", "full_name": "OK"},
    )
    response = client.post(
        "/api/v1/auth/login", json={"email": "ok@example.com", "password": "correct-horse-battery"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20


def test_login_with_wrong_password_rejected(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "ok2@example.com", "password": "correct-horse-battery", "full_name": "OK2"},
    )
    response = client.post(
        "/api/v1/auth/login", json={"email": "ok2@example.com", "password": "wrong-password"}
    )
    assert response.status_code == 401


def test_login_with_unknown_email_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login", json={"email": "ghost@example.com", "password": "whatever123"}
    )
    assert response.status_code == 401


def test_protected_endpoint_requires_token(client: TestClient) -> None:
    response = client.get("/api/v1/scans")
    assert response.status_code == 401


def test_protected_endpoint_rejects_garbage_token(client: TestClient) -> None:
    response = client.get("/api/v1/scans", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_protected_endpoint_accepts_valid_token(client: TestClient, auth_headers: dict) -> None:
    response = client.get("/api/v1/scans", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []
