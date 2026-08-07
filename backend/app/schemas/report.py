"""Response schema for a presigned report download URL."""

from pydantic import BaseModel


class ReportUrlRead(BaseModel):
    url: str
    expires_in: int
