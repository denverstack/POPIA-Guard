"""Scan endpoints: upload a ZIP to scan, list past scans, and view results."""

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import NotFoundError, StorageUnavailableError
from app.db.session import get_db
from app.models.user import User
from app.repositories.scan_repository import ScanRepository
from app.schemas.finding import FindingRead
from app.schemas.report import ReportUrlRead
from app.schemas.scan import ScanJobRead, ScanResultRead
from app.services.report.scoring import compute_compliance_percentage, compute_risk_score
from app.services.scan_service import run_zip_scan
from app.services.storage.s3_client import S3StorageService, StorageError

REPORT_URL_EXPIRY_SECONDS = 3600

router = APIRouter()


@router.post("", response_model=ScanResultRead, status_code=201)
async def create_scan(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScanResultRead:
    file_bytes = await file.read()
    outcome = run_zip_scan(
        db, user_id=current_user.id, filename=file.filename or "upload.zip", file_bytes=file_bytes
    )
    return ScanResultRead(
        **ScanJobRead.model_validate(outcome["scan_job"]).model_dump(),
        findings=[FindingRead.model_validate(f) for f in outcome["findings"]],
        risk_score=outcome["risk_score"],
        compliance_percentage=outcome["compliance_percentage"],
    )


@router.get("", response_model=list[ScanJobRead])
def list_scans(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[ScanJobRead]:
    return ScanRepository(db).list_scan_jobs(current_user.id)


@router.get("/{scan_id}", response_model=ScanResultRead)
def get_scan(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScanResultRead:
    """Returns the scan job plus its findings and a freshly-computed score.

    The score isn't persisted (no Report row yet — that lands in Phase 4
    alongside S3 storage), so it's recomputed from the persisted findings
    on every request. Cheap at this data size, and keeps scoring logic in
    exactly one place rather than duplicating it in the frontend.
    """
    repo = ScanRepository(db)
    scan_job = repo.get_scan_job(scan_id, current_user.id)
    if scan_job is None:
        raise NotFoundError("Scan not found")

    findings = repo.get_findings(scan_id)
    risk_score = compute_risk_score(findings)
    compliance_percentage = compute_compliance_percentage(risk_score)

    return ScanResultRead(
        **ScanJobRead.model_validate(scan_job).model_dump(),
        findings=[FindingRead.model_validate(f) for f in findings],
        risk_score=risk_score,
        compliance_percentage=compliance_percentage,
    )


@router.get("/{scan_id}/findings", response_model=list[FindingRead])
def get_scan_findings(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[FindingRead]:
    repo = ScanRepository(db)
    scan_job = repo.get_scan_job(scan_id, current_user.id)
    if scan_job is None:
        raise NotFoundError("Scan not found")
    return repo.get_findings(scan_id)


@router.get("/{scan_id}/report", response_model=ReportUrlRead)
def get_scan_report(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportUrlRead:
    """Returns a fresh presigned URL for downloading the report.

    404 covers two distinct cases the caller can't tell apart from the
    response alone: the scan doesn't exist/isn't yours, or the report
    was never stored (e.g. S3 was unreachable when the scan completed —
    see scan_service._try_store_report). Both mean "nothing to download
    right now," which is the only thing this endpoint promises.
    """
    repo = ScanRepository(db)
    scan_job = repo.get_scan_job(scan_id, current_user.id)
    if scan_job is None:
        raise NotFoundError("Scan not found")

    report = repo.get_report_by_scan_id(scan_id)
    if report is None:
        raise NotFoundError("No report is available for this scan")

    try:
        storage = S3StorageService()
        url = storage.generate_presigned_url(report.s3_key, expires_in=REPORT_URL_EXPIRY_SECONDS)
    except StorageError as exc:
        raise StorageUnavailableError("Report storage is temporarily unavailable") from exc

    return ReportUrlRead(url=url, expires_in=REPORT_URL_EXPIRY_SECONDS)
