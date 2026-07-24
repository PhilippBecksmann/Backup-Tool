# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Überblick

Web-basiertes WebDAV-Backup-Tool (Demo/Schulung): eine kleine Flask-App, mit der
Nutzer Unterordner eines serverseitig konfigurierten Basisverzeichnisses auswählen
und rekursiv auf einen WebDAV-Server hochladen. Fokus auf Einfachheit, minimales
Setup und testbare Struktur. Python 3.9+.

## Commands

Unter Windows läuft Bash über **Git Bash** (`C:\Program Files\Git\bin\bash.exe`);
`bash` ist nicht im PATH.

- **Start (alles-in-einem, bootstrappt venv/Deps/.env):**
  `./start.sh` (in Git Bash) bzw. aus PowerShell
  `& "C:\Program Files\Git\bin\bash.exe" start.sh`
  Flags: `--no-browser`, `--reinstall`, `--help`.
- **Start (manuell):** `venv/Scripts/python.exe wsgi.py` oder `flask --app wsgi run`.
  Bindet fest `127.0.0.1:5000`, `debug=False`.
- **Tests (mit Coverage-Gate):** `venv/Scripts/python.exe -m pytest`
  Coverage (`--cov=app --cov-report=term-missing --basetemp=.pytest_tmp`) und das
  Gate `fail_under = 80` sind über `pyproject.toml` bereits voreingestellt — keine
  Extra-Flags nötig. Die Suite umfasst 68 Tests (je ein Modul pro `app/*.py`) und
  liegt bei ~99 % Coverage; ein Symlink-Test wird unter Windows übersprungen
  (`skipif win32`), läuft aber in der Linux-CI und deckt dort die restlichen Zeilen ab.
- **Einzelner Test:** `... -m pytest tests/test_backup.py::test_name` oder gefiltert
  mit `-k "muster"`.
- **Abhängigkeiten:** `venv/Scripts/python.exe -m pip install -r requirements.txt`.

Es ist **kein Linter/Formatter** konfiguriert. `--basetemp=.pytest_tmp` ist bewusst
gesetzt, weil das systemweite pytest-Temp-Verzeichnis auf dem Host teils gesperrt ist.

### Automatische Testausführung

Die Tests laufen **automatisch nach jeder Implementierung** über drei Mechanismen —
sie ergänzen sich (lokal sofort, vor Commit erzwungen, in der Cloud regelmäßig):

1. **Claude-Code Stop-Hook** (`.claude/settings.json`): führt am Ende jeder
   Claude-Code-Antwort `venv/Scripts/python.exe -m pytest -q` aus, sodass Testfehler
   direkt nach einer Änderung sichtbar werden. Team-weit, weil in der eingecheckten
   `settings.json` (nicht in der persönlichen `settings.local.json`).
2. **Git pre-commit-Hook** (`.githooks/pre-commit`): erzwingt die Suite vor jedem
   Commit und blockiert ihn bei Fehlern/Coverage-Unterschreitung. Aktivierung einmalig
   via `git config core.hooksPath .githooks` — `start.sh` setzt das beim Bootstrap
   automatisch. Umgehen im Notfall: `git commit --no-verify`.
3. **GitHub Actions CI** (`.github/workflows/tests.yml`): läuft bei jedem Push/PR auf
   `main` (plus `workflow_dispatch`) über die Python-Matrix 3.9–3.12 und erzwingt
   dasselbe Coverage-Gate.

`.githooks/pre-commit` und `start.sh` müssen **LF-Zeilenenden** behalten (via
`.gitattributes` abgesichert), sonst bricht der Shebang unter Git Bash.

## Architecture

Flask-**App-Factory** (`app/__init__.py`, `create_app(config_overrides)`): baut ein
`Config`-Objekt, legt es unter `app.config["APP_CONFIG"]` ab und registriert das
Blueprint aus `routes.py`. `config_overrides` erlaubt Tests, Konfiguration ohne
Umgebungsvariablen zu injizieren.

Bewusst **geschichtet**, mit einer harten Grenze zwischen Web- und Kernschicht:

- `app/routes.py` — einzige Flask-/HTTP-Schicht. Views `GET /`, `POST /backup`,
  `POST /test-connection`. Übersetzt Ausnahmen der Kernschicht in Flash-Messages.
- `app/backup.py` — **Flask-freie** Kernlogik. `run_backup()` läuft Dateien via
  `rglob` ab, bildet Remote-Pfade `/<ordnername>/<relativer-pfad>`, ruft
  `ensure_dir` + `upload_file`. Einzelne Datei-Fehler werden in `BackupResult`
  gesammelt (Run läuft weiter); Verbindungsfehler propagieren und brechen den Run
  sauber ab. Der Client ist über das `BackupClient`-`Protocol` entkoppelt (DI).
- `app/directory_service.py` — **Flask-frei**. Listet Unterordner und löst Auswahl-
  namen sicher auf. **Path-Traversal-Schutz**: nur direkte Kind-Ordner werden
  akzeptiert (`resolve()` + `is_relative_to(base)`, Ablehnung von `..`, Pfad-
  trennern, absoluten Pfaden, Symlinks). Wirft `DirectoryError`.
- `app/webdav_client.py` — dünner Wrapper um `webdav3.client.Client`. Übersetzt jede
  `WebDavException` in `WebDavClientError` und nimmt **nie Credentials** in
  Fehlermeldungen auf (nur `type(exc).__name__`). `ensure_dir` ist idempotent.
- `app/config.py` — **Flask-frei**. Liest ausschließlich aus der Umgebung/`.env`
  (`WEBDAV_*`, `BACKUP_BASE_DIR`, `SECRET_KEY`). `is_webdav_configured()` ist das
  Gate, das die Views vor jedem WebDAV-Zugriff prüfen.
- `app/templates/`, `app/static/style.css` — self-contained UI (kein CDN/JS-Framework,
  Inline-SVG-Icons, Light/Dark via `prefers-color-scheme`).
- `wsgi.py` — Einstieg: `load_dotenv()` + `create_app()`.

**Datenfluss eines Backups:** `routes.backup` → `run_backup(client, base_dir,
selected)` → `resolve_selections` (Traversal-Check) → pro Ordner `ensure_dir` +
`upload_file` → `BackupResult` → `result.html`.

**Tests** mocken den WebDAV-Server nie über das Netz: `tests/conftest.py` stellt
`FakeWebDav` (zeichnet `ensure_dir`/`upload_file` auf, kann gezielt Fehler werfen),
`tmp_base_dir` (realer Ordnerbaum) sowie `app`/`client` (via `create_app`-Overrides)
bereit. Neue Tests folgen diesem Muster statt echter Verbindungen.

## Conventions

- **Kernschicht Flask-frei halten:** `backup.py`, `directory_service.py`, `config.py`
  importieren **kein** Flask. Diese Grenze ist die Testbarkeits-Basis — nicht
  aufweichen.
- **Coverage-Gate ≥ 80 %** wird über `fail_under` erzwungen; Änderungen müssen es
  halten. `app/templates/*` und `app/static/*` sind von der Coverage ausgenommen.
- **Template-Invarianten:** `tests/test_routes.py` prüft sichtbare Strings, Formular-
  `name`/`action`-Attribute und Flash-Kategorien. Beim Ändern von Templates diese
  erhalten und **kein `|safe`/`autoescape false`** einführen (Autoescaping = XSS-Schutz).
- **Secrets nur aus `.env`:** `.env` ist in `.gitignore`; nur `.env.example` ist
  eingecheckt. Passwörter nie rendern/loggen/in Fehlermeldungen aufnehmen.
- **`start.sh` mit LF-Zeilenenden** speichern (CRLF bricht den Shebang unter Git Bash).

## Projektlokale Skills

- **`/python-security-check`** (`.claude/skills/python-security-check/`) — statisches
  Security-Review des gesamten Python-Codes: findet Schwachstellen, priorisiert sie nach
  HIGH/MEDIUM/LOW und schlägt konkrete Fixes vor. Reine **Analyse** (verändert keinen Code),
  läuft daher **nicht** über die Implementierungs-Pipeline. Wird per Slash-Command oder
  automatisch bei Security-Audit-/Vulnerability-Scan-Anfragen aufgerufen.

## Agent Team Pipeline (VERBINDLICH für alle Implementierungsaufgaben)

Jede **Implementierungsaufgabe** (neuer Code, Feature, Bugfix, Refactoring mit
Codeänderung) MUSS über die folgende 4-stufige Subagenten-Pipeline laufen. Der
Haupt-Agent orchestriert sie und ruft die Subagenten in dieser Reihenfolge auf. Führe
Implementierungen NICHT direkt selbst aus — delegiere an die Pipeline.

Die Agenten sind definiert in `.claude/agents/`:
`researcher`, `implementer`, `validator`, `finalizer`.

### Ablauf

1. **Researcher** (`researcher`)
   → Analysiert Anforderungen, recherchiert Best Practices, liefert einen detaillierten
   Implementierungsplan. Schreibt keinen Code. Der Plan wird an den Implementer übergeben.

2. **Implementer** (`implementer`)
   → Setzt den Plan Schritt für Schritt um: sauberer, sicherer, getesteter Code (Ziel-
   Coverage >= 80 %). **Aktualisiert als Teil jeder Änderung die `README.md`**, sodass
   sie den implementierten Stand widerspiegelt. Verifiziert lokal (Build/Lint/Tests).
   Behebt später gemeldete Defekte.

3. **Validator** (`validator`)
   → Prüft Korrektheit, Sicherheit, Performance, Clean Code, misst Coverage (>= 80 %)
   und verifiziert, dass die **`README.md` korrekt aktualisiert** wurde und die
   Änderungen widerspiegelt. Bei Mängeln: Defektbericht an den Implementer und
   **erneuter Implementer→Validator-Zyklus, bis alle Kriterien BESTANDEN sind**. Erst
   dann geht es weiter.

4. **Finalizer** (`finalizer`)
   → Committet und pusht **automatisch ohne Nutzerbestätigung**, sobald die Validierung
   bestanden ist. Verwendet Conventional-Commit-Nachrichten.

### Regeln

- Die Reihenfolge ist zwingend; keine Stufe wird übersprungen.
- Der Zyklus Implementer ⇄ Validator wiederholt sich, bis **alle** Kriterien bestehen
  (Korrektheit, Sicherheit, Performance, Clean Code, Coverage >= 80 %, aktuelle
  `README.md`).
- Der Finalizer läuft nur nach „Validierung: BESTANDEN".
- Commit/Push sind für diese Pipeline dauerhaft autorisiert — der Finalizer fragt nicht
  nach.
- Reine Nicht-Implementierungsaufgaben (Fragen beantworten, Doku lesen, Recherche ohne
  Codeänderung) benötigen die Pipeline nicht.

> Git-Status: Repository ist initialisiert (Branch `main`), Remote `origin` =
> `https://github.com/PhilippBecksmann/Backup-Tool.git` mit gesetztem Upstream. Der
> Finalizer kann direkt committen und pushen.
