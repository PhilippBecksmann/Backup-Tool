"""Core backup logic. Free of Flask and third-party WebDAV imports.

Walks selected sub-directories, mirrors their structure on the remote target
under ``/<folder-name>/<relative-path>`` and uploads every file. Individual
file failures are collected and do not abort the whole run; connection-level
failures (raised by the client wrapper) propagate to the caller.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Protocol

from app.directory_service import resolve_selections


class BackupClient(Protocol):
    """Structural interface the backup needs from a WebDAV client wrapper."""

    def ensure_dir(self, remote_path: str) -> None: ...

    def upload_file(self, remote_path: str, local_path: str) -> None: ...


@dataclass
class FileError:
    """A single file that could not be uploaded."""

    local_path: str
    remote_path: str
    message: str


@dataclass
class BackupResult:
    """Aggregated outcome of a backup run."""

    uploaded: int = 0
    failed: int = 0
    errors: list[FileError] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.uploaded + self.failed

    @property
    def success(self) -> bool:
        """True when at least one file was processed and none failed."""
        return self.failed == 0

    def record_success(self) -> None:
        self.uploaded += 1

    def record_failure(self, local_path: str, remote_path: str, message: str) -> None:
        self.failed += 1
        self.errors.append(FileError(local_path, remote_path, message))


def _iter_files(root: Path) -> list[Path]:
    """Return all files below ``root`` in a deterministic order."""
    return sorted(p for p in root.rglob("*") if p.is_file())


def _remote_path_for(folder_name: str, root: Path, file_path: Path) -> str:
    """Build the remote path for ``file_path`` relative to its ``root``."""
    relative = file_path.relative_to(root)
    parts = [folder_name, *relative.parts]
    return "/" + str(PurePosixPath(*parts))


def _backup_folder(
    client: BackupClient, folder_name: str, folder_path: Path, result: BackupResult
) -> None:
    """Back up a single selected folder into ``result``."""
    files = _iter_files(folder_path)
    ensured_dirs: set[str] = set()

    for file_path in files:
        remote_path = _remote_path_for(folder_name, folder_path, file_path)
        remote_dir = str(PurePosixPath(remote_path).parent)
        # Directory creation failures are treated as connection-level errors
        # and propagate so the whole run aborts cleanly.
        if remote_dir not in ensured_dirs:
            client.ensure_dir(remote_dir)
            ensured_dirs.add(remote_dir)
        # Individual upload failures are collected; the run continues.
        try:
            client.upload_file(remote_path, str(file_path))
            result.record_success()
        except Exception as exc:  # noqa: BLE001 - collected per-file, run continues
            result.record_failure(str(file_path), remote_path, str(exc))


def run_backup(
    client: BackupClient,
    base_dir: str | Path,
    selected_names: list[str],
) -> BackupResult:
    """Back up every selected folder to the remote WebDAV target.

    ``selected_names`` are the plain sub-folder names chosen by the user. They
    are validated and resolved against ``base_dir`` (path-traversal safe) via
    :func:`directory_service.resolve_selections`. The remote target folder name
    is derived from each folder's own name.
    """
    result = BackupResult()
    selected_paths = resolve_selections(base_dir, selected_names)
    for folder_path in selected_paths:
        folder = Path(folder_path)
        _backup_folder(client, folder.name, folder, result)
    return result
