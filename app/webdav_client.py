"""Thin wrapper around :class:`webdav3.client.Client`.

Isolates the third-party WebDAV library behind a small, testable surface and
translates its exceptions into :class:`WebDavClientError`. Never logs or
embeds credentials in error messages.
"""

from __future__ import annotations

from pathlib import PurePosixPath

from webdav3.client import Client
from webdav3.exceptions import WebDavException


class WebDavClientError(Exception):
    """Raised when a WebDAV operation fails."""


def _normalize_remote(remote_path: str) -> str:
    """Normalize a remote path to a POSIX-style, leading-slash path."""
    cleaned = str(remote_path).replace("\\", "/").strip()
    if not cleaned.startswith("/"):
        cleaned = "/" + cleaned
    return cleaned


class WebDavBackupClient:
    """Convenience wrapper offering the operations the backup needs."""

    def __init__(self, options: dict[str, object], client: Client | None = None) -> None:
        """Create the wrapper.

        ``client`` may be injected for testing; otherwise a real
        ``webdav3.client.Client`` is built from ``options``.
        """
        self._client = client if client is not None else Client(options)

    def test_connection(self) -> bool:
        """Return True if the root collection is reachable.

        Raises :class:`WebDavClientError` on any WebDAV-level failure.
        """
        try:
            return bool(self._client.check("/"))
        except WebDavException as exc:
            raise WebDavClientError(
                f"WebDAV connection test failed: {type(exc).__name__}"
            ) from exc

    def ensure_dir(self, remote_path: str) -> None:
        """Create ``remote_path`` and all missing parents (idempotent)."""
        remote = _normalize_remote(remote_path)
        parts = [p for p in PurePosixPath(remote).parts if p != "/"]
        current = ""
        try:
            for part in parts:
                current = f"{current}/{part}"
                if not self._client.check(current):
                    self._client.mkdir(current)
        except WebDavException as exc:
            raise WebDavClientError(
                f"Failed to create remote directory {remote!r}: {type(exc).__name__}"
            ) from exc

    def upload_file(self, remote_path: str, local_path: str) -> None:
        """Upload a single local file to ``remote_path``."""
        remote = _normalize_remote(remote_path)
        try:
            self._client.upload_sync(remote_path=remote, local_path=str(local_path))
        except WebDavException as exc:
            raise WebDavClientError(
                f"Failed to upload {remote!r}: {type(exc).__name__}"
            ) from exc
