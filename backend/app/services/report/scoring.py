"""Turns a set of findings into a risk score and compliance percentage.
See docs/SCANNER_DESIGN.md for the rationale — this is intentionally a
simple, explainable weighted sum, not a statistical model.

Deliberately decoupled from any specific Finding type via a structural
Protocol: it's called both with freshly-produced `ScanFinding` objects
(right after a scan) and with persisted `Finding` ORM rows (when
re-deriving a score for a past scan on GET /scans/{id}) — both merely
need a `.severity` attribute, so there's exactly one scoring
implementation rather than two.
"""

from collections.abc import Sequence
from typing import Protocol

_SEVERITY_WEIGHTS = {
    "critical": 10,
    "high": 5,
    "medium": 2,
    "low": 1,
}


class _HasSeverity(Protocol):
    severity: str


def compute_risk_score(findings: Sequence[_HasSeverity]) -> float:
    raw = sum(_SEVERITY_WEIGHTS.get(f.severity, 0) for f in findings)
    return float(min(100, raw))


def compute_compliance_percentage(risk_score: float) -> float:
    return float(max(0.0, 100.0 - risk_score))
