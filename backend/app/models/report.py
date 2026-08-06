"""Report model — one row per generated compliance report.

Stores the S3 object key, not a presigned URL: presigned URLs expire, so a
fresh one is generated on read (see app/services/storage).
"""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.scan import ScanJob


class ReportFormat(str, enum.Enum):
    JSON = "json"
    HTML = "html"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    scan_job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scan_jobs.id"), unique=True, nullable=False
    )
    format: Mapped[str] = mapped_column(String(10), default=ReportFormat.JSON.value)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    compliance_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    s3_key: Mapped[str] = mapped_column(String(500), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    scan_job: Mapped["ScanJob"] = relationship(back_populates="report")
