"""Integration tests for the scan upload API — exercises the full pipeline
end to end: upload -> extract -> scan -> persist -> score -> respond.
"""

import io
import zipfile

from fastapi.testclient import TestClient


def _build_zip(files: dict[str, str]) -> io.BytesIO:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    buffer.seek(0)
    return buffer


def test_scan_upload_detects_findings_and_computes_score(
    client: TestClient, auth_headers: dict
) -> None:
    zip_buffer = _build_zip(
        {
            "src/config.py": "AWS_ACCESS_KEY_ID = 'AKIAABCDEFGHIJKLMNOP'\n",
            "src/seed_data.py": "contact_email = 'jane.doe@example.co.za'\n",
            "README.md": "This project has no secrets in it.\n",
        }
    )

    response = client.post(
        "/api/v1/scans",
        headers=auth_headers,
        files={"file": ("upload.zip", zip_buffer, "application/zip")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert body["files_scanned"] == 3

    rule_ids = {f["rule_id"] for f in body["findings"]}
    assert "secret.aws_access_key" in rule_ids
    assert "popia.email" in rule_ids

    # AWS key (critical, weight 10) + email (medium, weight 2) = 12
    assert body["risk_score"] == 12.0
    assert body["compliance_percentage"] == 88.0

    # Raw secret value must never appear in the response.
    raw_response_text = response.text
    assert "AKIAABCDEFGHIJKLMNOP" not in raw_response_text


def test_scan_upload_rejects_non_zip_file(client: TestClient, auth_headers: dict) -> None:
    response = client.post(
        "/api/v1/scans",
        headers=auth_headers,
        files={"file": ("notes.txt", io.BytesIO(b"just text"), "text/plain")},
    )
    assert response.status_code == 400


def test_scan_upload_rejects_corrupt_zip(client: TestClient, auth_headers: dict) -> None:
    response = client.post(
        "/api/v1/scans",
        headers=auth_headers,
        files={"file": ("upload.zip", io.BytesIO(b"not actually a zip"), "application/zip")},
    )
    assert response.status_code == 400


def test_scan_upload_requires_auth(client: TestClient) -> None:
    zip_buffer = _build_zip({"a.py": "x = 1\n"})
    response = client.post(
        "/api/v1/scans", files={"file": ("upload.zip", zip_buffer, "application/zip")}
    )
    assert response.status_code == 401


def test_list_scans_returns_only_own_scans(client: TestClient) -> None:
    # User A registers, logs in, and uploads a scan.
    client.post(
        "/api/v1/auth/register",
        json={"email": "a@example.com", "password": "correct-horse-battery", "full_name": "A"},
    )
    login_a = client.post(
        "/api/v1/auth/login", json={"email": "a@example.com", "password": "correct-horse-battery"}
    )
    headers_a = {"Authorization": f"Bearer {login_a.json()['access_token']}"}
    client.post(
        "/api/v1/scans",
        headers=headers_a,
        files={"file": ("upload.zip", _build_zip({"x.py": "x = 1\n"}), "application/zip")},
    )

    # User B registers and logs in, but never uploads anything.
    client.post(
        "/api/v1/auth/register",
        json={"email": "b@example.com", "password": "correct-horse-battery", "full_name": "B"},
    )
    login_b = client.post(
        "/api/v1/auth/login", json={"email": "b@example.com", "password": "correct-horse-battery"}
    )
    headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

    response_a = client.get("/api/v1/scans", headers=headers_a)
    response_b = client.get("/api/v1/scans", headers=headers_b)

    assert len(response_a.json()) == 1
    assert len(response_b.json()) == 0


def test_get_scan_not_owned_by_user_returns_404(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "owner@example.com", "password": "correct-horse-battery", "full_name": "O"},
    )
    login_owner = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@example.com", "password": "correct-horse-battery"},
    )
    headers_owner = {"Authorization": f"Bearer {login_owner.json()['access_token']}"}
    upload_response = client.post(
        "/api/v1/scans",
        headers=headers_owner,
        files={"file": ("upload.zip", _build_zip({"x.py": "x = 1\n"}), "application/zip")},
    )
    scan_id = upload_response.json()["id"]

    client.post(
        "/api/v1/auth/register",
        json={
            "email": "intruder@example.com",
            "password": "correct-horse-battery",
            "full_name": "I",
        },
    )
    login_intruder = client.post(
        "/api/v1/auth/login",
        json={"email": "intruder@example.com", "password": "correct-horse-battery"},
    )
    headers_intruder = {"Authorization": f"Bearer {login_intruder.json()['access_token']}"}

    response = client.get(f"/api/v1/scans/{scan_id}", headers=headers_intruder)
    assert response.status_code == 404


def test_get_scan_findings(client: TestClient, auth_headers: dict) -> None:
    zip_buffer = _build_zip({"secret.py": "password = 'sup3rSecretValue'\n"})
    upload_response = client.post(
        "/api/v1/scans",
        headers=auth_headers,
        files={"file": ("upload.zip", zip_buffer, "application/zip")},
    )
    scan_id = upload_response.json()["id"]

    response = client.get(f"/api/v1/scans/{scan_id}/findings", headers=auth_headers)
    assert response.status_code == 200
    findings = response.json()
    assert len(findings) == 1
    assert findings[0]["rule_id"] == "secret.generic_credential"


def test_get_scan_detail_returns_findings_and_recomputed_score(
    client: TestClient, auth_headers: dict
) -> None:
    zip_buffer = _build_zip(
        {"config.py": "AWS_ACCESS_KEY_ID = 'AKIAABCDEFGHIJKLMNOP'\n"}
    )
    upload_response = client.post(
        "/api/v1/scans",
        headers=auth_headers,
        files={"file": ("upload.zip", zip_buffer, "application/zip")},
    )
    scan_id = upload_response.json()["id"]

    # A fresh GET (simulating revisiting the page later) should return the
    # same findings and score as the original upload response — computed
    # from persisted findings, not a stashed value from the upload call.
    response = client.get(f"/api/v1/scans/{scan_id}", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body["findings"]) == 1
    assert body["findings"][0]["rule_id"] == "secret.aws_access_key"
    assert body["risk_score"] == 10.0  # critical severity weight
    assert body["compliance_percentage"] == 90.0
