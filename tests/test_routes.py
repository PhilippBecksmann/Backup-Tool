"""Tests for the Flask routes."""

from __future__ import annotations

import pytest

from app import routes
from app.backup import BackupResult
from app.config import Config
from app.webdav_client import WebDavClientError


def _configure_webdav(app):
    """Replace the app's config object with a fully configured one."""
    app.config["APP_CONFIG"] = Config(
        env={
            "WEBDAV_HOSTNAME": "https://h",
            "WEBDAV_LOGIN": "l",
            "WEBDAV_PASSWORD": "p",
        }
    )


def test_index_lists_folders(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "docs" in body
    assert "photos" in body


def test_index_without_base_dir(app):
    app.config["BACKUP_BASE_DIR"] = ""
    resp = app.test_client().get("/")
    assert resp.status_code == 200
    assert "Kein Basisverzeichnis" in resp.get_data(as_text=True)


def test_backup_empty_selection_redirects(client):
    resp = client.post("/backup", data={}, follow_redirects=True)
    assert resp.status_code == 200
    assert "mindestens einen Ordner" in resp.get_data(as_text=True)


def test_backup_not_configured(client):
    resp = client.post(
        "/backup", data={"folders": ["docs"]}, follow_redirects=True
    )
    assert "nicht vollständig konfiguriert" in resp.get_data(as_text=True)


def test_backup_success(app, monkeypatch):
    _configure_webdav(app)

    result = BackupResult()
    result.record_success()

    monkeypatch.setattr(routes, "run_backup", lambda *a, **k: result)
    monkeypatch.setattr(
        routes, "WebDavBackupClient", lambda *a, **k: object()
    )

    resp = app.test_client().post("/backup", data={"folders": ["docs"]})
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Backup-Ergebnis" in body
    assert "erfolgreich gesichert" in body


def test_backup_connection_error(app, monkeypatch):
    _configure_webdav(app)

    def boom(*a, **k):
        raise WebDavClientError("down")

    monkeypatch.setattr(routes, "run_backup", boom)
    monkeypatch.setattr(routes, "WebDavBackupClient", lambda *a, **k: object())

    resp = app.test_client().post(
        "/backup", data={"folders": ["docs"]}, follow_redirects=True
    )
    assert "fehlgeschlagen" in resp.get_data(as_text=True)


def test_backup_invalid_selection(app, monkeypatch):
    _configure_webdav(app)
    monkeypatch.setattr(routes, "WebDavBackupClient", lambda *a, **k: object())

    resp = app.test_client().post(
        "/backup", data={"folders": ["../escape"]}, follow_redirects=True
    )
    assert "Ungültige Ordnerauswahl" in resp.get_data(as_text=True)


def test_test_connection_success(app, monkeypatch):
    _configure_webdav(app)

    class OkClient:
        def test_connection(self):
            return True

    monkeypatch.setattr(routes, "WebDavBackupClient", lambda *a, **k: OkClient())
    resp = app.test_client().post("/test-connection", follow_redirects=True)
    assert "erfolgreich" in resp.get_data(as_text=True)


def test_test_connection_failure(app, monkeypatch):
    _configure_webdav(app)

    class BadClient:
        def test_connection(self):
            raise WebDavClientError("nope")

    monkeypatch.setattr(routes, "WebDavBackupClient", lambda *a, **k: BadClient())
    resp = app.test_client().post("/test-connection", follow_redirects=True)
    assert "fehlgeschlagen" in resp.get_data(as_text=True)


def test_test_connection_not_configured(client):
    resp = client.post("/test-connection", follow_redirects=True)
    assert "nicht vollständig konfiguriert" in resp.get_data(as_text=True)


def test_index_bad_base_dir(app):
    app.config["BACKUP_BASE_DIR"] = "/nonexistent/xyz/123"
    resp = app.test_client().get("/")
    assert resp.status_code == 200
    # DirectoryError message is flashed.
    assert "does not exist" in resp.get_data(as_text=True)
