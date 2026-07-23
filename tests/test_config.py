"""Tests for app.config."""

from __future__ import annotations

import pytest

from app.config import Config, _parse_bool, _parse_int


def test_defaults_when_env_empty():
    cfg = Config(env={})
    assert cfg.WEBDAV_TIMEOUT == 30
    assert cfg.WEBDAV_VERIFY_SSL is True
    assert cfg.TESTING is False
    assert cfg.SECRET_KEY == "dev-insecure-secret-key"
    assert cfg.is_webdav_configured() is False


def test_full_env_is_configured():
    cfg = Config(
        env={
            "WEBDAV_HOSTNAME": "https://example.com/dav",
            "WEBDAV_LOGIN": "user",
            "WEBDAV_PASSWORD": "secret",
            "BACKUP_BASE_DIR": "/data",
            "SECRET_KEY": "abc",
            "WEBDAV_TIMEOUT": "45",
            "WEBDAV_VERIFY_SSL": "false",
        }
    )
    assert cfg.is_webdav_configured() is True
    assert cfg.WEBDAV_TIMEOUT == 45
    assert cfg.WEBDAV_VERIFY_SSL is False
    assert cfg.SECRET_KEY == "abc"


def test_webdav_options_shape():
    cfg = Config(
        env={
            "WEBDAV_HOSTNAME": "https://h",
            "WEBDAV_LOGIN": "l",
            "WEBDAV_PASSWORD": "p",
        }
    )
    options = cfg.webdav_options()
    assert options["webdav_hostname"] == "https://h"
    assert options["webdav_login"] == "l"
    assert options["webdav_password"] == "p"
    assert options["verify"] is True


def test_as_flask_config():
    cfg = Config(env={"BACKUP_BASE_DIR": "/x", "SECRET_KEY": "k"})
    flask_cfg = cfg.as_flask_config()
    assert flask_cfg["BACKUP_BASE_DIR"] == "/x"
    assert flask_cfg["SECRET_KEY"] == "k"
    assert flask_cfg["TESTING"] is False


@pytest.mark.parametrize(
    "value,expected",
    [
        ("true", True),
        ("1", True),
        ("YES", True),
        ("on", True),
        ("false", False),
        ("0", False),
        ("no", False),
        ("", True),  # empty -> default
        (None, True),  # missing -> default
    ],
)
def test_parse_bool(value, expected):
    assert _parse_bool(value, default=True) is expected


def test_parse_bool_invalid():
    with pytest.raises(ValueError):
        _parse_bool("maybe", default=True)


def test_parse_int_default_and_invalid():
    assert _parse_int(None, default=7) == 7
    assert _parse_int("", default=7) == 7
    assert _parse_int("12", default=7) == 12
    with pytest.raises(ValueError):
        _parse_int("abc", default=7)


def test_missing_password_not_configured():
    cfg = Config(env={"WEBDAV_HOSTNAME": "h", "WEBDAV_LOGIN": "l"})
    assert cfg.is_webdav_configured() is False
