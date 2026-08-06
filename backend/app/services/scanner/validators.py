"""Validators referenced by detection rules.

A bare regex over-matches for a couple of the POPIA categories — these
functions are the second check that keeps precision reasonable. Each takes
`(matched_text, line)` and returns whether the match should be kept.
"""

import re

_BANK_CONTEXT_KEYWORDS = (
    "account",
    "acc_no",
    "acc no",
    "bank",
    "iban",
    "sort code",
    "branch code",
)


def validate_sa_id(matched_text: str, line: str) -> bool:  # noqa: ARG001
    """South African ID numbers are 13 digits: YYMMDD + gender/citizenship
    digits + a checksum digit. This checks both the date prefix is
    plausible and the checksum is correct — a bare 13-digit regex alone
    matches far too many unrelated numbers (phone numbers, IDs from other
    countries, timestamps).
    """
    if not matched_text.isdigit() or len(matched_text) != 13:
        return False

    if not _has_plausible_date_prefix(matched_text):
        return False

    return _sa_id_checksum_is_valid(matched_text)


def _has_plausible_date_prefix(digits: str) -> bool:
    month = int(digits[2:4])
    day = int(digits[4:6])
    return 1 <= month <= 12 and 1 <= day <= 31


def _sa_id_checksum_is_valid(digits: str) -> bool:
    values = [int(d) for d in digits]

    # Sum of digits at odd positions (1-indexed): 1, 3, 5, 7, 9, 11
    odd_sum = sum(values[i] for i in range(0, 12, 2))

    # Digits at even positions (1-indexed): 2, 4, 6, 8, 10, 12, concatenated
    # as a number, doubled, then digit-summed.
    even_digits = "".join(str(values[i]) for i in range(1, 12, 2))
    doubled = int(even_digits) * 2
    even_sum = sum(int(d) for d in str(doubled))

    total = odd_sum + even_sum
    check_digit = (10 - (total % 10)) % 10

    return check_digit == values[12]


def validate_bank_account_context(matched_text: str, line: str) -> bool:  # noqa: ARG001
    """A bare 9-11 digit number matches all kinds of things that aren't
    bank accounts (line numbers, timestamps, phone numbers without a
    prefix). Require a banking-related keyword nearby on the same line.
    """
    lowered = line.lower()
    return any(keyword in lowered for keyword in _BANK_CONTEXT_KEYWORDS)


_JWT_SHAPE = re.compile(r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$")


def validate_jwt_shape(matched_text: str, line: str) -> bool:  # noqa: ARG001
    """Confirms the three dot-separated segments look base64url-ish, to
    filter out incidental three-dot-joined strings that aren't tokens.
    """
    return bool(_JWT_SHAPE.match(matched_text))
