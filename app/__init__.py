"""Flask application factory."""

from __future__ import annotations

from flask import Flask

from app.config import Config


def create_app(config_overrides: dict[str, object] | None = None) -> Flask:
    """Create and configure the Flask application.

    ``config_overrides`` lets tests inject configuration (e.g. TESTING,
    BACKUP_BASE_DIR) without touching the process environment.
    """
    app = Flask(__name__)

    config = Config()
    app.config.update(config.as_flask_config())
    # Keep the parsed Config object available to views.
    app.config["APP_CONFIG"] = config

    if config_overrides:
        app.config.update(config_overrides)

    from app.routes import bp

    app.register_blueprint(bp)
    return app
