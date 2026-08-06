"""Safe ZIP extraction.

A naive `ZipFile.extractall()` is vulnerable to "zip slip": a malicious
archive entry named e.g. `../../etc/cron.d/evil` or an absolute path can
write outside the intended extraction directory. For a tool whose whole
purpose is security scanning, shipping that vulnerability in the upload
path itself would be a bad look — this checks every member's resolved
path stays inside the destination before extracting anything.
"""

import zipfile
from pathlib import Path

from app.core.exceptions import UnsupportedUploadError


def _is_within_directory(directory: Path, target: Path) -> bool:
    try:
        target.relative_to(directory)
    except ValueError:
        return False
    return True


def safe_extract(zip_path: Path, dest: Path) -> None:
    dest = dest.resolve()

    try:
        with zipfile.ZipFile(zip_path) as zf:
            for member in zf.infolist():
                member_path = (dest / member.filename).resolve()
                if not _is_within_directory(dest, member_path):
                    raise UnsupportedUploadError(
                        f"Archive contains an unsafe path: {member.filename}"
                    )
            zf.extractall(dest)
    except zipfile.BadZipFile as exc:
        raise UnsupportedUploadError("Uploaded file is not a valid zip archive") from exc
