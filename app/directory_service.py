"""Directory listing and safe selection resolution.

Free of Flask imports. Guards against path traversal by only accepting names
that resolve to a direct child of the configured base directory.
"""

from __future__ import annotations

from pathlib import Path


class DirectoryError(Exception):
    """Raised when a directory cannot be listed or a selection is invalid."""


def _resolved_base(base_dir: str | Path) -> Path:
    """Resolve the base directory and ensure it exists and is a directory."""
    base = Path(base_dir).expanduser().resolve()
    if not base.is_dir():
        raise DirectoryError(f"Base directory does not exist: {base}")
    return base


def list_subdirectories(base_dir: str | Path) -> list[str]:
    """Return the names of the immediate sub-directories of ``base_dir``.

    Symlinked directories are skipped to avoid escaping the base directory.
    The result is sorted alphabetically for stable rendering.
    """
    base = _resolved_base(base_dir)
    names: list[str] = []
    for entry in base.iterdir():
        if entry.is_symlink():
            continue
        if entry.is_dir():
            names.append(entry.name)
    return sorted(names)


def resolve_selection(base_dir: str | Path, name: str) -> Path:
    """Resolve a single selected sub-folder name to an absolute path.

    Rejects anything that is not a plain, direct child directory of the base:
    empty names, path separators, ``..``, absolute paths and symlinks that
    lead outside the base directory. Raises :class:`DirectoryError` on any
    violation.
    """
    base = _resolved_base(base_dir)

    if not isinstance(name, str) or name.strip() == "":
        raise DirectoryError("Empty selection name")

    # Reject any name that carries a directory component or drive/anchor.
    if name != Path(name).name:
        raise DirectoryError(f"Invalid selection name: {name!r}")
    if name in (".", ".."):
        raise DirectoryError(f"Invalid selection name: {name!r}")

    candidate = (base / name).resolve()

    # The resolved candidate must stay strictly inside the base directory.
    if candidate == base or not candidate.is_relative_to(base):
        raise DirectoryError(f"Selection escapes base directory: {name!r}")

    if (base / name).is_symlink():
        raise DirectoryError(f"Symlinked selections are not allowed: {name!r}")

    if not candidate.is_dir():
        raise DirectoryError(f"Selection is not a directory: {name!r}")

    return candidate


def resolve_selections(base_dir: str | Path, names: list[str]) -> list[Path]:
    """Resolve multiple selection names, raising on the first invalid one."""
    return [resolve_selection(base_dir, name) for name in names]
