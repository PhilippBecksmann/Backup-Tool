"""HTTP routes for the backup web UI."""

from __future__ import annotations

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from app.backup import run_backup
from app.config import Config
from app.directory_service import DirectoryError, list_subdirectories
from app.webdav_client import WebDavBackupClient, WebDavClientError

bp = Blueprint("main", __name__)


def _config() -> Config:
    return current_app.config["APP_CONFIG"]


def _base_dir() -> str:
    return current_app.config.get("BACKUP_BASE_DIR", "")


def _load_folders() -> list[str]:
    """List selectable sub-folders, flashing a message on failure."""
    base_dir = _base_dir()
    if not base_dir:
        flash("Kein Basisverzeichnis konfiguriert (BACKUP_BASE_DIR).", "error")
        return []
    try:
        return list_subdirectories(base_dir)
    except DirectoryError as exc:
        flash(str(exc), "error")
        return []


def _build_client() -> WebDavBackupClient:
    return WebDavBackupClient(_config().webdav_options())


@bp.get("/")
def index() -> str:
    folders = _load_folders()
    return render_template(
        "index.html",
        folders=folders,
        webdav_configured=_config().is_webdav_configured(),
    )


@bp.post("/test-connection")
def test_connection():
    if not _config().is_webdav_configured():
        flash("WebDAV ist nicht vollständig konfiguriert.", "error")
        return redirect(url_for("main.index"))
    try:
        _build_client().test_connection()
        flash("Verbindung zum WebDAV-Server erfolgreich.", "success")
    except WebDavClientError:
        flash("Verbindung zum WebDAV-Server fehlgeschlagen.", "error")
    return redirect(url_for("main.index"))


@bp.post("/backup")
def backup():
    selected = request.form.getlist("folders")
    if not selected:
        flash("Bitte mindestens einen Ordner auswählen.", "error")
        return redirect(url_for("main.index"))

    if not _config().is_webdav_configured():
        flash("WebDAV ist nicht vollständig konfiguriert.", "error")
        return redirect(url_for("main.index"))

    try:
        client = _build_client()
        result = run_backup(client, _base_dir(), selected)
    except DirectoryError:
        flash("Ungültige Ordnerauswahl.", "error")
        return redirect(url_for("main.index"))
    except WebDavClientError:
        flash("Verbindung zum WebDAV-Server fehlgeschlagen. Backup abgebrochen.", "error")
        return redirect(url_for("main.index"))

    return render_template("result.html", result=result, selected=selected)
