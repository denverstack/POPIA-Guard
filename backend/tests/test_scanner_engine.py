"""Unit tests for the detection engine. Each POPIA and secret rule gets a
positive case (should be detected) and, where the rule has a validator, a
negative case (should be filtered out) — the validators exist specifically
to cut false positives, so that's the behaviour worth locking in with tests.
"""

from pathlib import Path

from app.services.scanner.engine import redact, scan_directory


def _write(tmp_path: Path, name: str, content: str) -> None:
    (tmp_path / name).write_text(content, encoding="utf-8")


def _rule_ids(findings) -> set[str]:
    return {f.rule_id for f in findings}


class TestPopiaDetection:
    def test_detects_valid_sa_id_number(self, tmp_path: Path) -> None:
        _write(tmp_path, "seed_data.py", "test_user_id = '8001015009087'\n")
        findings = scan_directory(tmp_path)
        assert "popia.sa_id_number" in _rule_ids(findings)

    def test_rejects_random_13_digit_number_failing_checksum(self, tmp_path: Path) -> None:
        # Same length and shape as an SA ID but with a broken checksum digit.
        _write(tmp_path, "config.py", "REQUEST_TIMEOUT_MS = 1234567890123\n")
        findings = scan_directory(tmp_path)
        assert "popia.sa_id_number" not in _rule_ids(findings)

    def test_detects_email_address(self, tmp_path: Path) -> None:
        _write(tmp_path, "fixtures.json", '{"contact": "jane.doe@example.co.za"}\n')
        findings = scan_directory(tmp_path)
        assert "popia.email" in _rule_ids(findings)

    def test_detects_sa_mobile_number(self, tmp_path: Path) -> None:
        _write(tmp_path, "contacts.csv", "name,phone\nJane,+27821234567\n")
        findings = scan_directory(tmp_path)
        assert "popia.phone_number" in _rule_ids(findings)

    def test_detects_sa_mobile_number_with_leading_zero(self, tmp_path: Path) -> None:
        _write(tmp_path, "contacts.csv", "name,phone\nJane,0821234567\n")
        findings = scan_directory(tmp_path)
        assert "popia.phone_number" in _rule_ids(findings)

    def test_detects_bank_account_with_context(self, tmp_path: Path) -> None:
        _write(tmp_path, "invoice_template.py", "bank_account_number = '123456789'\n")
        findings = scan_directory(tmp_path)
        assert "popia.bank_account" in _rule_ids(findings)

    def test_ignores_long_number_without_bank_context(self, tmp_path: Path) -> None:
        _write(tmp_path, "constants.py", "MAX_BUFFER_SIZE = 123456789\n")
        findings = scan_directory(tmp_path)
        assert "popia.bank_account" not in _rule_ids(findings)


class TestSecretDetection:
    def test_detects_aws_access_key(self, tmp_path: Path) -> None:
        _write(tmp_path, ".env.bak", "AWS_ACCESS_KEY_ID=AKIAABCDEFGHIJKLMNOP\n")
        findings = scan_directory(tmp_path)
        assert "secret.aws_access_key" in _rule_ids(findings)

    def test_detects_github_token(self, tmp_path: Path) -> None:
        token = "ghp_" + "a" * 36
        _write(tmp_path, "deploy.sh", f"export GH_TOKEN={token}\n")
        findings = scan_directory(tmp_path)
        assert "secret.github_token" in _rule_ids(findings)

    def test_detects_jwt(self, tmp_path: Path) -> None:
        header = "eyJhbGciOiJIUzI1NiJ9"
        payload = "eyJzdWIiOiIxMjM0NTY3ODkwIn0"
        signature = "dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PYAOYWi9E5eE"
        fake_jwt = f"{header}.{payload}.{signature}"
        _write(tmp_path, "test_auth.py", f'token = "{fake_jwt}"\n')
        findings = scan_directory(tmp_path)
        assert "secret.jwt" in _rule_ids(findings)

    def test_detects_generic_password_assignment(self, tmp_path: Path) -> None:
        _write(tmp_path, "settings.py", "password = 'sup3rSecretValue'\n")
        findings = scan_directory(tmp_path)
        assert "secret.generic_credential" in _rule_ids(findings)

    def test_generic_credential_redacts_value_not_keyword(self, tmp_path: Path) -> None:
        _write(tmp_path, "settings.py", "password = 'sup3rSecretValue'\n")
        findings = scan_directory(tmp_path)
        match = next(f for f in findings if f.rule_id == "secret.generic_credential")
        # The redacted snippet should be a masked form of the value alone,
        # not the "password = " prefix.
        assert match.matched_snippet.startswith("su")
        assert "password" not in match.matched_snippet


class TestEngineBehaviour:
    def test_skips_vendored_directories(self, tmp_path: Path) -> None:
        vendored = tmp_path / "node_modules" / "some_pkg"
        vendored.mkdir(parents=True)
        _write(vendored, "index.js", "const key = 'AKIAABCDEFGHIJKLMNOP';\n")
        findings = scan_directory(tmp_path)
        assert findings == []

    def test_skips_binary_files_without_raising(self, tmp_path: Path) -> None:
        (tmp_path / "photo.png").write_bytes(b"\x89PNG\r\n\x1a\n" + bytes(range(255)) * 4)
        findings = scan_directory(tmp_path)
        assert findings == []

    def test_finding_includes_correct_file_path_and_line_number(self, tmp_path: Path) -> None:
        _write(tmp_path, "notes.txt", "line one\nline two\nemail: someone@example.com\n")
        findings = scan_directory(tmp_path)
        match = next(f for f in findings if f.rule_id == "popia.email")
        assert match.file_path == "notes.txt"
        assert match.line_number == 3

    def test_no_findings_in_clean_file(self, tmp_path: Path) -> None:
        _write(tmp_path, "clean.py", "def add(a, b):\n    return a + b\n")
        assert scan_directory(tmp_path) == []


class TestRedact:
    def test_redact_masks_middle_keeps_ends(self) -> None:
        assert redact("AKIAABCDEFGHIJKLMNOP") == "AK****************OP"

    def test_redact_short_value_fully_masked(self) -> None:
        assert redact("abcd") == "****"
