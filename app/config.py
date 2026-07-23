"""Application configuration loaded from environment variables.

This module is intentionally free of Flask imports so that the configuration
logic stays easy to test in isolation.
"""

from __future__ import annotations

import os


_TRUE_VALUES = {"1", "true", "yes", "on", "y", "t"}
_FALSE_VALUES = {"0", "false", "no", "off", "n", "f"}

DEFAULT_WEBDAV_TIMEOUT = 30


def _parse_bool(value: str | None, *, default: bool) -> bool:
    """Parse a string into a boolean, falling back to ``default``.

    Recognises common truthy/falsy spellings case-insensitively. Unknown
    values raise ``ValueError`` so misconfiguration is surfaced early.
    """
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized == "":
        return default
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ValueError(f"Cannot parse boolean from value: {value!r}")


def _parse_int(value: str | None, *, default: int) -> int:
    """Parse a string into an int, falling back to ``default`` when empty."""
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Cannot parse integer from value: {value!r}") from exc


class Config:
    """Runtime configuration for the backup application.

    Values are read from the process environment. Missing WebDAV credentials
    are tolerated at construction time (the application still starts) but the
    :meth:`webdav_options` helper reports whether the configuration is complete.
    """

    def __init__(self, env: dict[str, str] | None = None) -> None:
        source = os.environ if env is None else env

        self.WEBDAV_HOSTNAME = source.get("WEBDAV_HOSTNAME", "").strip()
        self.WEBDAV_LOGIN = source.get("WEBDAV_LOGIN", "").strip()
        self.WEBDAV_PASSWORD = source.get("WEBDAV_PASSWORD", "")
        self.BACKUP_BASE_DIR = source.get("BACKUP_BASE_DIR", "").strip()
        self.SECRET_KEY = source.get("SECRET_KEY", "").strip() or "dev-insecure-secret-key"
        self.WEBDAV_TIMEOUT = _parse_int(
            source.get("WEBDAV_TIMEOUT"), default=DEFAULT_WEBDAV_TIMEOUT
        )
        self.WEBDAV_VERIFY_SSL = _parse_bool(
            source.get("WEBDAV_VERIFY_SSL"), default=True
        )
        self.TESTING = _parse_bool(source.get("TESTING"), default=False)

    def is_webdav_configured(self) -> bool:
        """Return True when all mandatory WebDAV settings are present."""
        return bool(
            self.WEBDAV_HOSTNAME and self.WEBDAV_LOGIN and self.WEBDAV_PASSWORD
        )

    def webdav_options(self) -> dict[str, object]:
        """Build the options dict expected by ``webdav3.client.Client``."""
        return {
            "webdav_hostname": self.WEBDAV_HOSTNAME,
            "webdav_login": self.WEBDAV_LOGIN,
            "webdav_password": self.WEBDAV_PASSWORD,
            "webdav_timeout": self.WEBDAV_TIMEOUT,
            "verify": self.WEBDAV_VERIFY_SSL,
        }

    def as_flask_config(self) -> dict[str, object]:
        """Expose the subset of settings Flask itself needs."""
        return {
            "SECRET_KEY": self.SECRET_KEY,
            "TESTING": self.TESTING,
            "BACKUP_BASE_DIR": self.BACKUP_BASE_DIR,
        }
