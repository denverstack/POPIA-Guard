"""Builds the JSON report document uploaded to S3.

A deliberately plain, complete JSON dump of a scan's results — the API
already exposes the same data structurally (see ScanResultRead); this is
the durable, downloadable artifact of it.
"""

import json

from app.core.time import utcnow
from app.models.finding import Finding
from app.models.scan import ScanJob


def build_report_document(
    scan_job: ScanJob,
    findings: list[Finding],
    risk_score: float,
    compliance_percentage: float,
) -> bytes:
    document = {
        "scan_id": scan_job.id,
        "source_type": scan_job.source_type,
        "source_reference": scan_job.source_reference,
        "generated_at": utcnow().isoformat(),
        "files_scanned": scan_job.files_scanned,
        "risk_score": risk_score,
        "compliance_percentage": compliance_percentage,
        "findings": [
            {
                "category": f.category,
                "rule_id": f.rule_id,
                "severity": f.severity,
                "file_path": f.file_path,
                "line_number": f.line_number,
                "matched_snippet": f.matched_snippet,
            }
            for f in findings
        ],
    }
    return json.dumps(document, indent=2).encode("utf-8")
