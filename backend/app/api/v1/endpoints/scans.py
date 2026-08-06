"""Scan endpoints: upload a ZIP to scan, list past scans, and view results."""

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.models.user import User
from app.repositories.scan_repository import ScanRepository
from app.schemas.finding import FindingRead
from app.schemas.scan import ScanJobRead, ScanResultRead
from app.services.scan_service import run_zip_scan

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


@router.get("/{scan_id}", response_model=ScanJobRead)
def get_scan(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScanJobRead:
    scan_job = ScanRepository(db).get_scan_job(scan_id, current_user.id)
    if scan_job is None:
        raise NotFoundError("Scan not found")
    return scan_job


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
