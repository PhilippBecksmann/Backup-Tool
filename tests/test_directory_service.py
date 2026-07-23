"""Tests for app.directory_service."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from app.directory_service import (
    DirectoryError,
    list_subdirectories,
    resolve_selection,
    resolve_selections,
)


def test_list_subdirectories(tmp_base_dir: Path):
    assert list_subdirectories(tmp_base_dir) == ["docs", "empty", "photos"]


def test_list_nonexistent_base(tmp_path: Path):
    with pytest.raises(DirectoryError):
        list_subdirectories(tmp_path / "missing")


def test_list_empty_base(tmp_path: Path):
    empty = tmp_path / "empty_base"
    empty.mkdir()
    assert list_subdirectories(empty) == []


def test_resolve_valid_selection(tmp_base_dir: Path):
    resolved = resolve_selection(tmp_base_dir, "docs")
    assert resolved == (tmp_base_dir / "docs").resolve()


def test_resolve_selections_multiple(tmp_base_dir: Path):
    resolved = resolve_selections(tmp_base_dir, ["docs", "photos"])
    assert [p.name for p in resolved] == ["docs", "photos"]


@pytest.mark.parametrize("name", ["", "   ", ".", ".."])
def test_reject_empty_or_dot(tmp_base_dir: Path, name: str):
    with pytest.raises(DirectoryError):
        resolve_selection(tmp_base_dir, name)


@pytest.mark.parametrize(
    "name",
    ["../secret", "docs/sub", "sub\\deep", "/etc/passwd", "docs/../photos"],
)
def test_reject_path_traversal(tmp_base_dir: Path, name: str):
    with pytest.raises(DirectoryError):
        resolve_selection(tmp_base_dir, name)


def test_reject_absolute_path(tmp_base_dir: Path, tmp_path: Path):
    outside = tmp_path / "outside"
    outside.mkdir()
    with pytest.raises(DirectoryError):
        resolve_selection(tmp_base_dir, str(outside))


def test_reject_file_selection(tmp_base_dir: Path):
    with pytest.raises(DirectoryError):
        resolve_selection(tmp_base_dir, "loose.txt")


def test_reject_nonexistent_selection(tmp_base_dir: Path):
    with pytest.raises(DirectoryError):
        resolve_selection(tmp_base_dir, "does_not_exist")


def test_reject_non_string(tmp_base_dir: Path):
    with pytest.raises(DirectoryError):
        resolve_selection(tmp_base_dir, None)  # type: ignore[arg-type]


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Symlink creation typically requires privileges on Windows.",
)
def test_symlink_directory_skipped_and_rejected(tmp_path: Path):
    base = tmp_path / "base"
    base.mkdir()
    real_outside = tmp_path / "outside"
    real_outside.mkdir()
    (base / "real").mkdir()

    link = base / "link"
    link.symlink_to(real_outside, target_is_directory=True)

    # Symlinked dirs are not listed.
    assert list_subdirectories(base) == ["real"]
    # And cannot be resolved as a selection.
    with pytest.raises(DirectoryError):
        resolve_selection(base, "link")
