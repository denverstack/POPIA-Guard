"""Data access for ScanJob, Finding, and Report."""

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.finding import Finding
from app.models.report import Report
from app.models.scan import ScanJob


class ScanRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_scan_job(
        self, *, user_id: str, source_type: str, source_reference: str
    ) -> ScanJob:
        scan_job = ScanJob(
            user_id=user_id, source_type=source_type, source_reference=source_reference
        )
        self.db.add(scan_job)
        self.db.commit()
        self.db.refresh(scan_job)
        return scan_job

    def get_scan_job(self, scan_id: str, user_id: str) -> ScanJob | None:
        """Scoped to the owning user — this is what prevents one user from
        reading another user's scan by guessing an id.
        """
        return (
            self.db.query(ScanJob)
            .filter(ScanJob.id == scan_id, ScanJob.user_id == user_id)
            .first()
        )

    def list_scan_jobs(self, user_id: str) -> list[ScanJob]:
        return (
            self.db.query(ScanJob)
            .filter(ScanJob.user_id == user_id)
            .order_by(ScanJob.created_at.desc())
            .all()
        )

    def update_status(
        self,
        scan_job: ScanJob,
        *,
        status: str,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        files_scanned: int | None = None,
    ) -> ScanJob:
        scan_job.status = status
        if started_at is not None:
            scan_job.started_at = started_at
        if completed_at is not None:
            scan_job.completed_at = completed_at
        if files_scanned is not None:
            scan_job.files_scanned = files_scanned
        self.db.commit()
        self.db.refresh(scan_job)
        return scan_job

    def add_findings(self, scan_job_id: str, findings: list[dict[str, Any]]) -> list[Finding]:
        rows = [Finding(scan_job_id=scan_job_id, **f) for f in findings]
        self.db.add_all(rows)
        self.db.commit()
        for row in rows:
            self.db.refresh(row)
        return rows

    def get_findings(self, scan_job_id: str) -> list[Finding]:
        return (
            self.db.query(Finding)
            .filter(Finding.scan_job_id == scan_job_id)
            .order_by(Finding.severity.desc(), Finding.file_path)
            .all()
        )

    def create_report(
        self,
        *,
        scan_job_id: str,
        risk_score: float,
        compliance_percentage: float,
        s3_key: str,
        format: str = "json",
    ) -> Report:
        report = Report(
            scan_job_id=scan_job_id,
            risk_score=risk_score,
            compliance_percentage=compliance_percentage,
            s3_key=s3_key,
            format=format,
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_report_by_scan_id(self, scan_job_id: str) -> Report | None:
        return self.db.query(Report).filter(Report.scan_job_id == scan_job_id).first()
