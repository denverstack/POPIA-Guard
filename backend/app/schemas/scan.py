"""Response schemas for scan jobs and scan results."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.finding import FindingRead


class ScanJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_type: str
    source_reference: str
    status: str
    files_scanned: int
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class ScanResultRead(ScanJobRead):
    """Returned immediately after a scan completes: the job plus its
    findings and computed score. Not persisted as a `Report` row yet —
    report persistence + S3 upload land in Phase 4.
    """

    findings: list[FindingRead]
    risk_score: float
    compliance_percentage: float
