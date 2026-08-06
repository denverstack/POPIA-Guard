"""Response schema for a single detection."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category: str
    rule_id: str
    severity: str
    file_path: str
    line_number: int
    matched_snippet: str
    created_at: datetime
