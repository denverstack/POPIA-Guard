"""Small time helper.

`datetime.utcnow()` is deprecated (removal scheduled in a future Python
version). The replacement, `datetime.now(UTC)`, returns a timezone-aware
datetime — but our DateTime columns aren't declared `timezone=True`, so
storing a tz-aware value would be inconsistent across SQLite and Postgres.
This keeps the naive-UTC convention the columns already expect while
avoiding the deprecated call.
"""

from datetime import UTC, datetime


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
