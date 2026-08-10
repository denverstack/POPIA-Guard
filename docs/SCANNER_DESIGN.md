# Scanner Engine Design

This is the design for the detection engine implemented in Phase 2
(`app/services/scanner/`). It's written now, ahead of the implementation,
so the pattern set and architecture are decided deliberately rather than
grown ad hoc.

## Goal

Walk a source tree (an uploaded ZIP, extracted; or a cloned GitHub repo),
and for every text file, run a registry of detection rules against its
content, producing `Finding` records (see `docs/DATABASE.md`).

## Detection categories (lean scope)

**POPIA data categories**  four, chosen because they're both common in
seeded test data/fixtures and unambiguous enough to detect with reasonable
precision:

| Rule ID              | What it catches                          | Validation                                  |
|-----------------------|-------------------------------------------|----------------------------------------------|
| `popia.sa_id_number`  | South African 13-digit ID numbers         | Luhn-style checksum on the last digit, plus a plausible YYMMDD prefix. This is what keeps it from matching arbitrary 13-digit strings |
| `popia.email`         | Email addresses                           | Standard email regex |
| `popia.phone_number`  | South African phone numbers (`+27`/`0` prefixed) | Digit count + prefix check |
| `popia.bank_account`  | Bank account number patterns near banking keywords | Regex plus a proximity check for words like `account`, `acc_no`, `iban` in the same line reduces false positives on arbitrary long digit strings |

**Secret categories** — four, matching the most common leak types seen in
real incident reports:

| Rule ID                  | What it catches                          |
|----------------------------|-------------------------------------------|
| `secret.aws_access_key`    | `AKIA[0-9A-Z]{16}` pattern                |
| `secret.github_token`      | `gh[pousr]_[A-Za-z0-9]{36,}` pattern      |
| `secret.jwt`                | Three base64url segments joined by `.`   |
| `secret.generic_credential` | `password`/`secret`/`api_key` assignment followed by a non-trivial literal string |

Each rule maps to a fixed severity (`critical` for AWS/GitHub keys and SA ID
numbers, `high` for JWTs and bank accounts, `medium` for email/phone). 
Severity is a property of the rule, not computed per-match, which keeps
scoring simple and explainable.

## Engine architecture

```
services/scanner/
    engine.py            # orchestrates: walk tree -> run rules -> yield findings
    patterns/
        popia_patterns.py    # rule definitions: id, regex, severity, category
        secret_patterns.py
    validators.py         # checksum / proximity checks referenced by rules
```

A rule is a small dataclass: `id`, `category`, `severity`, `pattern`
(compiled regex), and an optional `validator` callable that takes the
regex match and surrounding line and returns `True`/`False`. Most rules
don't need a validator — the SA ID and bank account rules do, since a bare
regex alone produces too many false positives on those.

The engine itself is deliberately simple: read a file as text (skip
anything that fails UTF-8 decoding. Treated as binary), iterate lines,
run every rule's regex against each line, call the validator if present,
and yield a finding for each match that survives validation.

## What's explicitly excluded (and why)

- **No entropy-based generic secret detection.** Shannon entropy scanning
  catches more secret shapes but produces enough false positives on
  minified JS/hashes/UUIDs that it needs its own tuning pass. Out of scope
  for this project's demonstration goal.
- **No custom pattern configuration UI.** Rules are defined in code, not
  user-editable at runtime. Reasonable for a v1; a real product would need
  this, but it's a feature addition, not core to demonstrating the engine.
- **Skip paths:** `node_modules/`, `.git/`, `venv/`, `.venv/`, `dist/`,
  `build/` are excluded by default. Scanning vendored/generated code
  produces noise, not signal.

## Scoring

Each `ScanJob`'s `Report` gets:

- **`risk_score`** — weighted sum of findings by severity
  (`critical`×10, `high`×5, `medium`×2, `low`×1), capped and normalised to
  a 0–100 scale.
- **`compliance_percentage`** — `100 - risk_score`, floored at 0. Simple
  by design: it's meant to give a directional signal on the dashboard, not
  stand in for a real compliance audit.
