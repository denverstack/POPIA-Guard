"""POPIA-sensitive data detection rules. See docs/SCANNER_DESIGN.md for the
rationale behind each rule and its validator.
"""

import re

from app.models.finding import FindingCategory, Severity
from app.services.scanner.rules import Rule
from app.services.scanner.validators import validate_bank_account_context, validate_sa_id

POPIA_RULES: list[Rule] = [
    Rule(
        id="popia.sa_id_number",
        category=FindingCategory.POPIA.value,
        severity=Severity.CRITICAL.value,
        pattern=re.compile(r"\b\d{13}\b"),
        validator=validate_sa_id,
    ),
    Rule(
        id="popia.email",
        category=FindingCategory.POPIA.value,
        severity=Severity.MEDIUM.value,
        pattern=re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    ),
    Rule(
        id="popia.phone_number",
        category=FindingCategory.POPIA.value,
        severity=Severity.MEDIUM.value,
        # South African mobile numbers: +27 or leading 0, then 6/7/8, then 8 digits.
        # Note: \b doesn't work as a boundary before "+" (not a word character),
        # so the +27 branch uses a negative lookbehind for a preceding digit instead.
        pattern=re.compile(r"(?:(?<!\d)\+27[678]\d{8}\b|\b0[678]\d{8}\b)"),
    ),
    Rule(
        id="popia.bank_account",
        category=FindingCategory.POPIA.value,
        severity=Severity.HIGH.value,
        pattern=re.compile(r"\b\d{9,11}\b"),
        validator=validate_bank_account_context,
    ),
]
