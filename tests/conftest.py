"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from app import create_app
from app.webdav_client import WebDavClientError


@pytest.fixture
def tmp_base_dir(tmp_path: Path) -> Path:
    """Create a realistic base directory with nested folders and files."""
    base = tmp_path / "base"
    base.mkdir()

    docs = base / "docs"
    docs.mkdir()
    (docs / "readme.txt").write_text("hello", encoding="utf-8")
    (docs / "sub").mkdir()
    (docs / "sub" / "note.md").write_text("note", encoding="utf-8")

    photos = base / "photos"
    photos.mkdir()
    (photos / "a.jpg").write_bytes(b"\x00\x01")

    empty = base / "empty"
    empty.mkdir()

    # A loose file at the base level (not selectable as a folder).
    (base / "loose.txt").write_text("loose", encoding="utf-8")

    return base


class FakeWebDav:
    """Records WebDAV operations and can be told to fail on demand."""

    def __init__(self) -> None:
        self.ensured_dirs: list[str] = []
        self.uploads: list[tuple[str, str]] = []
        self.connected = True
        self.fail_ensure_on: set[str] = set()
        self.fail_upload_on: set[str] = set()

    def ensure_dir(self, remote_path: str) -> None:
        if remote_path in self.fail_ensure_on:
            raise WebDavClientError("ensure_dir failed")
        self.ensured_dirs.append(remote_path)

    def upload_file(self, remote_path: str, local_path: str) -> None:
        if remote_path in self.fail_upload_on:
            raise WebDavClientError("upload failed")
        self.uploads.append((remote_path, local_path))

    def test_connection(self) -> bool:
        if not self.connected:
            raise WebDavClientError("not connected")
        return True


@pytest.fixture
def fake_webdav() -> FakeWebDav:
    return FakeWebDav()


@pytest.fixture
def app(tmp_base_dir: Path):
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "BACKUP_BASE_DIR": str(tmp_base_dir),
        }
    )
    return application


@pytest.fixture
def client(app):
    return app.test_client()
