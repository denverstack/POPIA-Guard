"""Orchestrates a full scan run: extract the upload, run the detection
engine, persist findings, compute the score. This is the business logic
the API layer delegates to — the endpoint itself stays thin.
"""

import logging
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import TypedDict

from sqlalchemy.orm import Session

from app.core.exceptions import UnsupportedUploadError
from app.core.time import utcnow
from app.models.finding import Finding
from app.models.scan import ScanJob, ScanStatus, SourceType
from app.repositories.scan_repository import ScanRepository
from app.services.archive import safe_extract
from app.services.report.scoring import compute_compliance_percentage, compute_risk_score
from app.services.scanner.engine import scan_directory

logger = logging.getLogger(__name__)

MAX_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024  # 20MB — a deliberate, simple guard;
# see docs/SCANNER_DESIGN.md for what's out of scope (full zip-bomb defence).


class ScanOutcome(TypedDict):
    scan_job: ScanJob
    findings: list[Finding]
    risk_score: float
    compliance_percentage: float


def run_zip_scan(
    db: Session, *, user_id: str, filename: str, file_bytes: bytes
) -> ScanOutcome:
    if not filename.lower().endswith(".zip"):
        raise UnsupportedUploadError("Only .zip uploads are supported")

    if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise UnsupportedUploadError(
            f"File exceeds the {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB upload limit"
        )

    repo = ScanRepository(db)
    scan_job = repo.create_scan_job(
        user_id=user_id, source_type=SourceType.UPLOAD.value, source_reference=filename
    )
    repo.update_status(scan_job, status=ScanStatus.RUNNING.value, started_at=utcnow())
    logger.info("scan started scan_id=%s user_id=%s filename=%s", scan_job.id, user_id, filename)

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            zip_path = tmp_path / "upload.zip"
            zip_path.write_bytes(file_bytes)

            extract_dir = tmp_path / "extracted"
            extract_dir.mkdir()
            safe_extract(zip_path, extract_dir)

            scan_findings = scan_directory(extract_dir)
            files_scanned = sum(1 for p in extract_dir.rglob("*") if p.is_file())
    except UnsupportedUploadError:
        repo.update_status(
            scan_job, status=ScanStatus.FAILED.value, completed_at=utcnow()
        )
        logger.warning("scan failed scan_id=%s user_id=%s", scan_job.id, user_id)
        raise

    findings = repo.add_findings(scan_job.id, [asdict(f) for f in scan_findings])
    risk_score = compute_risk_score(scan_findings)
    compliance_percentage = compute_compliance_percentage(risk_score)

    scan_job = repo.update_status(
        scan_job,
        status=ScanStatus.COMPLETED.value,
        completed_at=utcnow(),
        files_scanned=files_scanned,
    )
    logger.info(
        "scan completed scan_id=%s findings=%d risk_score=%.1f",
        scan_job.id,
        len(findings),
        risk_score,
    )

    return ScanOutcome(
        scan_job=scan_job,
        findings=findings,
        risk_score=risk_score,
        compliance_percentage=compliance_percentage,
    )
