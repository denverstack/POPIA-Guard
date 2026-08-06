"""Turns a set of findings into a risk score and compliance percentage.
See docs/SCANNER_DESIGN.md for the rationale — this is intentionally a
simple, explainable weighted sum, not a statistical model.
"""

from app.services.scanner.engine import ScanFinding

_SEVERITY_WEIGHTS = {
    "critical": 10,
    "high": 5,
    "medium": 2,
    "low": 1,
}


def compute_risk_score(findings: list[ScanFinding]) -> float:
    raw = sum(_SEVERITY_WEIGHTS.get(f.severity, 0) for f in findings)
    return float(min(100, raw))


def compute_compliance_percentage(risk_score: float) -> float:
    return float(max(0.0, 100.0 - risk_score))
