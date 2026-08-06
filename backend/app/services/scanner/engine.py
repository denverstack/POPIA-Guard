"""Scanner engine: walks a directory tree and runs the full rule registry
against every text file it finds. See docs/SCANNER_DESIGN.md for the design
rationale.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from app.services.scanner.patterns.popia_patterns import POPIA_RULES
from app.services.scanner.patterns.secret_patterns import SECRET_RULES
from app.services.scanner.rules import Rule

ALL_RULES: list[Rule] = [*POPIA_RULES, *SECRET_RULES]

# Vendored/generated directories carry noise, not signal — see design doc.
SKIP_DIRS = {"node_modules", ".git", "venv", ".venv", "dist", "build", "__pycache__"}

# Skip anything obviously binary before attempting a decode, purely as a
# fast-path optimisation; the UTF-8 decode check below is the real filter.
_BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".gz", ".tar",
    ".woff", ".woff2", ".ttf", ".eot", ".mp3", ".mp4", ".exe", ".dll", ".so",
    ".pyc", ".class", ".jar",
}


@dataclass
class ScanFinding:
    file_path: str
    line_number: int
    rule_id: str
    category: str
    severity: str
    matched_snippet: str


def redact(value: str) -> str:
    """Mask the middle of a matched value, keeping just enough of the ends
    to be recognisable without storing the raw sensitive data.
    """
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + "*" * (len(value) - 4) + value[-2:]


def _iter_text_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.suffix.lower() in _BINARY_EXTENSIONS:
            continue
        yield path


def _matched_value(match: re.Match[str]) -> str:
    """Use the first capture group if the rule's pattern defines one (so
    only the sensitive literal gets redacted, not a keyword prefix);
    otherwise fall back to the whole match.
    """
    if match.groups():
        return match.group(1)
    return match.group(0)


def scan_directory(root: Path, rules: list[Rule] | None = None) -> list[ScanFinding]:
    """Run every rule in `rules` (default: the full registry) against every
    text file under `root`. Returns findings with redacted snippets —
    the raw sensitive value never leaves this function.
    """
    active_rules = rules if rules is not None else ALL_RULES
    findings: list[ScanFinding] = []

    for file_path in _iter_text_files(root):
        try:
            text = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        relative_path = str(file_path.relative_to(root))

        for line_number, line in enumerate(text.splitlines(), start=1):
            for rule in active_rules:
                for match in rule.pattern.finditer(line):
                    matched_text = _matched_value(match)
                    if rule.validator and not rule.validator(matched_text, line):
                        continue

                    findings.append(
                        ScanFinding(
                            file_path=relative_path,
                            line_number=line_number,
                            rule_id=rule.id,
                            category=rule.category,
                            severity=rule.severity,
                            matched_snippet=redact(matched_text),
                        )
                    )

    return findings
