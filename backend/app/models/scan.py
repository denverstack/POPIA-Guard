"""ScanJob model — one row per scan run (ZIP upload or GitHub repo)."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.finding import Finding
    from app.models.report import Report
    from app.models.user import User


class SourceType(str, enum.Enum):
    UPLOAD = "upload"
    GITHUB = "github"


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScanJob(Base):
    __tablename__ = "scan_jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=ScanStatus.PENDING.value, nullable=False
    )
    files_scanned: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped["User"] = relationship(back_populates="scan_jobs")
    findings: Mapped[list["Finding"]] = relationship(
        back_populates="scan_job", cascade="all, delete-orphan"
    )
    report: Mapped["Report | None"] = relationship(
        back_populates="scan_job", cascade="all, delete-orphan", uselist=False
    )
