"""Tests for app.backup core logic."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.backup import BackupResult, _remote_path_for, run_backup
from app.directory_service import DirectoryError
from app.webdav_client import WebDavClientError


def test_backup_result_properties():
    result = BackupResult()
    assert result.total == 0
    # No files processed -> not a success.
    result.record_success()
    assert result.success is True
    result.record_failure("l", "r", "boom")
    assert result.success is False
    assert result.total == 2
    assert result.errors[0].message == "boom"


def test_remote_path_for(tmp_path: Path):
    root = tmp_path / "docs"
    root.mkdir()
    (root / "sub").mkdir()
    f = root / "sub" / "note.md"
    f.write_text("x", encoding="utf-8")
    assert _remote_path_for("docs", root, f) == "/docs/sub/note.md"


def test_backup_uploads_all_files(tmp_base_dir: Path, fake_webdav):
    result = run_backup(fake_webdav, tmp_base_dir, ["docs"])
    assert result.uploaded == 2
    assert result.failed == 0
    remote_paths = sorted(p for p, _ in fake_webdav.uploads)
    assert remote_paths == ["/docs/readme.txt", "/docs/sub/note.md"]


def test_backup_multiple_folders(tmp_base_dir: Path, fake_webdav):
    result = run_backup(fake_webdav, tmp_base_dir, ["docs", "photos"])
    assert result.uploaded == 3
    assert result.success is True


def test_backup_empty_folder(tmp_base_dir: Path, fake_webdav):
    result = run_backup(fake_webdav, tmp_base_dir, ["empty"])
    assert result.total == 0
    assert fake_webdav.uploads == []


def test_backup_single_file_failure_continues(tmp_base_dir: Path, fake_webdav):
    fake_webdav.fail_upload_on = {"/docs/readme.txt"}
    result = run_backup(fake_webdav, tmp_base_dir, ["docs"])
    assert result.uploaded == 1
    assert result.failed == 1
    assert result.success is False
    assert result.errors[0].remote_path == "/docs/readme.txt"


def test_backup_ensure_dir_failure_aborts(tmp_base_dir: Path, fake_webdav):
    fake_webdav.fail_ensure_on = {"/docs"}
    with pytest.raises(WebDavClientError):
        run_backup(fake_webdav, tmp_base_dir, ["docs"])


def test_backup_invalid_selection_raises(tmp_base_dir: Path, fake_webdav):
    with pytest.raises(DirectoryError):
        run_backup(fake_webdav, tmp_base_dir, ["../escape"])


def test_backup_ensure_dir_called_once_per_dir(tmp_base_dir: Path, fake_webdav):
    run_backup(fake_webdav, tmp_base_dir, ["docs"])
    # /docs and /docs/sub -> two distinct ensured dirs, no duplicates.
    assert sorted(fake_webdav.ensured_dirs) == ["/docs", "/docs/sub"]
