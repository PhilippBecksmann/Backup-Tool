"""Tests for app.webdav_client using a mocked underlying client."""

from __future__ import annotations

import pytest
from webdav3.exceptions import WebDavException

from app.webdav_client import WebDavBackupClient, WebDavClientError, _normalize_remote


class MockClient:
    """Minimal stand-in for webdav3.client.Client."""

    def __init__(self):
        self.existing: set[str] = set()
        self.made_dirs: list[str] = []
        self.uploads: list[tuple[str, str]] = []
        self.check_raises = False
        self.mkdir_raises = False
        self.upload_raises = False

    def check(self, remote_path):
        if self.check_raises:
            raise WebDavException("check failed")
        return remote_path in self.existing

    def mkdir(self, remote_path):
        if self.mkdir_raises:
            raise WebDavException("mkdir failed")
        self.made_dirs.append(remote_path)
        self.existing.add(remote_path)

    def upload_sync(self, remote_path, local_path):
        if self.upload_raises:
            raise WebDavException("upload failed")
        self.uploads.append((remote_path, local_path))


@pytest.fixture
def mock_client():
    return MockClient()


@pytest.fixture
def wrapper(mock_client):
    return WebDavBackupClient(options={}, client=mock_client)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("docs/file", "/docs/file"),
        ("/docs/file", "/docs/file"),
        ("docs\\sub\\f", "/docs/sub/f"),
        ("  /a/b  ", "/a/b"),
    ],
)
def test_normalize_remote(raw, expected):
    assert _normalize_remote(raw) == expected


def test_test_connection_ok(wrapper, mock_client):
    mock_client.existing.add("/")
    assert wrapper.test_connection() is True


def test_test_connection_failure(wrapper, mock_client):
    mock_client.check_raises = True
    with pytest.raises(WebDavClientError):
        wrapper.test_connection()


def test_ensure_dir_creates_missing_parents(wrapper, mock_client):
    wrapper.ensure_dir("/docs/sub")
    assert mock_client.made_dirs == ["/docs", "/docs/sub"]


def test_ensure_dir_idempotent(wrapper, mock_client):
    mock_client.existing.update({"/docs", "/docs/sub"})
    wrapper.ensure_dir("/docs/sub")
    assert mock_client.made_dirs == []


def test_ensure_dir_wraps_exception(wrapper, mock_client):
    mock_client.mkdir_raises = True
    with pytest.raises(WebDavClientError):
        wrapper.ensure_dir("/docs")


def test_upload_file_delegates(wrapper, mock_client):
    wrapper.upload_file("/docs/f.txt", "/local/f.txt")
    assert mock_client.uploads == [("/docs/f.txt", "/local/f.txt")]


def test_upload_file_wraps_exception(wrapper, mock_client):
    mock_client.upload_raises = True
    with pytest.raises(WebDavClientError):
        wrapper.upload_file("/docs/f.txt", "/local/f.txt")


def test_errors_do_not_leak_credentials(mock_client):
    mock_client.upload_raises = True
    wrapper = WebDavBackupClient(
        options={"webdav_password": "topsecret"}, client=mock_client
    )
    try:
        wrapper.upload_file("/docs/f.txt", "/local/f.txt")
    except WebDavClientError as exc:
        assert "topsecret" not in str(exc)


def test_constructor_builds_real_client(monkeypatch):
    created = {}

    class FakeReal:
        def __init__(self, options):
            created["options"] = options

    monkeypatch.setattr("app.webdav_client.Client", FakeReal)
    WebDavBackupClient(options={"webdav_hostname": "h"})
    assert created["options"] == {"webdav_hostname": "h"}
