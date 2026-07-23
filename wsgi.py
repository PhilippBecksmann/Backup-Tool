"""WSGI entry point.

Loads environment variables from a local ``.env`` file (if present) and builds
the Flask application via the factory. Run with:

    flask --app wsgi run
    python wsgi.py
"""

from dotenv import load_dotenv

from app import create_app

load_dotenv()

app = create_app()


if __name__ == "__main__":
    # debug is intentionally False; enable manually for local development only.
    app.run(host="127.0.0.1", port=5000, debug=False)
