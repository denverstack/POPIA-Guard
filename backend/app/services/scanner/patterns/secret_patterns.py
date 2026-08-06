"""Secret and credential detection rules. See docs/SCANNER_DESIGN.md."""

import re

from app.models.finding import FindingCategory, Severity
from app.services.scanner.rules import Rule
from app.services.scanner.validators import validate_jwt_shape

SECRET_RULES: list[Rule] = [
    Rule(
        id="secret.aws_access_key",
        category=FindingCategory.SECRET.value,
        severity=Severity.CRITICAL.value,
        pattern=re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    ),
    Rule(
        id="secret.github_token",
        category=FindingCategory.SECRET.value,
        severity=Severity.CRITICAL.value,
        pattern=re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    ),
    Rule(
        id="secret.jwt",
        category=FindingCategory.SECRET.value,
        severity=Severity.HIGH.value,
        # JWTs are base64url header.payload.signature; the header segment
        # for the common {"alg":...} shape starts with "eyJ".
        pattern=re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"),
        validator=validate_jwt_shape,
    ),
    Rule(
        id="secret.generic_credential",
        category=FindingCategory.SECRET.value,
        severity=Severity.HIGH.value,
        # password/secret/api_key assignment followed by a non-trivial quoted literal.
        pattern=re.compile(
            r"(?i)\b(?:password|secret|api[_-]?key)\s*[:=]\s*['\"]([^'\"\s]{6,})['\"]"
        ),
    ),
]
