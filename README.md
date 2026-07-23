# WebDAV Backup Tool (Demo)

Eine kleine, lokal laufende Flask-Webanwendung, mit der du aus einem
serverseitig konfigurierten Basisverzeichnis Unterordner auswählst und deren
Inhalte rekursiv zu einem WebDAV-Server hochlädst (Backup).

Der Fokus liegt auf einer schlichten, sauberen UI, minimalem Setup und einer
testbaren Struktur (Coverage >= 80 %). Die Kernlogik (`app/backup.py`,
`app/directory_service.py`) ist bewusst frei von Flask-Imports.

## Features

- Auswahl direkter Unterordner des konfigurierten `BACKUP_BASE_DIR` per Checkbox.
- Rekursiver Upload zu einem WebDAV-Ziel unter `/<ordnername>/<relativer-pfad>`.
- Idempotentes Anlegen der Zielverzeichnisse (`mkdir` nur bei Bedarf).
- Optionaler „Verbindung testen"-Button.
- Ergebnisseite mit Anzahl erfolgreicher/fehlgeschlagener Dateien und Fehlerliste.
- Robuste Fehlerbehandlung: einzelne fehlgeschlagene Dateien brechen das Backup
  nicht ab; Verbindungs-/Verzeichnisfehler brechen sauber ab.

## Oberfläche / UI

Die Weboberfläche ist bewusst modern und ohne externe Abhängigkeiten gestaltet:

- Karten-Layout mit Gradient-Header und Inline-SVG-Icons (Cloud-Upload, Ordner,
  Plug, Status). Keine externen Fonts, CDNs oder JavaScript-Bibliotheken — alles
  ist self-contained in `app/static/style.css` und den Templates.
- Automatischer **Light-/Dark-Mode** über `prefers-color-scheme`; das gesamte
  Styling basiert auf CSS-Custom-Properties.
- **Responsive** ab ca. 320 px Breite (Ordner-Kacheln und Statistik-Grid brechen
  auf schmalen Displays einspaltig um).
- Barrierefreiheit: AA-Kontraste, sichtbarer `:focus-visible`-Ring,
  `label`-verknüpfte Checkboxen, `role="alert"`/`role="status"` für Meldungen,
  `aria-hidden` an dekorativen SVGs sowie Respektierung von
  `prefers-reduced-motion`.
- Ordnerauswahl als klickbare Kacheln; der Auswahlzustand wird rein per CSS
  (`:has(input:checked)`) dargestellt und funktioniert ohne JavaScript.

## Nicht-Ziele (bewusst außerhalb des Umfangs)

Kein Download/Restore, keine Inkremental-Logik, keine Nutzerverwaltung/Login,
keine Datenbank, keine Zeitplanung, kein Multi-User-Deployment, kein nativer
OS-Datei-Auswahldialog, keine Zeitstempel-Ordner.

## Voraussetzungen

- Python 3.9 oder neuer (getestet mit Python 3.14).
- Ein erreichbarer WebDAV-Server samt Zugangsdaten.

## Installation

PowerShell (Windows):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Bash (Linux/macOS):

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Konfiguration

Kopiere `.env.example` nach `.env` und passe die Werte an. **Niemals** eine
echte `.env` einchecken (sie steht in `.gitignore`).

| Variable            | Pflicht | Default                    | Beschreibung                                                                 |
| ------------------- | :-----: | -------------------------- | ---------------------------------------------------------------------------- |
| `WEBDAV_HOSTNAME`   |   ja    | –                          | Basis-URL des WebDAV-Servers inkl. Schema.                                   |
| `WEBDAV_LOGIN`      |   ja    | –                          | Benutzername.                                                                |
| `WEBDAV_PASSWORD`   |   ja    | –                          | Passwort. Wird nie gerendert, geloggt oder in Fehlermeldungen aufgenommen.   |
| `BACKUP_BASE_DIR`   |   ja    | –                          | Absoluter Pfad, dessen Unterordner sicherbar sind (Path-Traversal-Grenze).   |
| `SECRET_KEY`        |  empf.  | `dev-insecure-secret-key`  | Flask-Secret zum Signieren der Session (Flash-Messages).                     |
| `WEBDAV_TIMEOUT`    |  nein   | `30`                       | Verbindungs-Timeout in Sekunden.                                             |
| `WEBDAV_VERIFY_SSL` |  nein   | `true`                     | TLS-Zertifikat prüfen. Nur für vertrauenswürdige Testserver deaktivieren.    |

Einen sicheren `SECRET_KEY` erzeugen:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Start

PowerShell oder Bash:

```bash
flask --app wsgi run
```

Alternativ direkt:

```bash
python wsgi.py
```

Danach im Browser `http://127.0.0.1:5000/` öffnen. `debug` ist absichtlich
auf `False` gesetzt.

## Schnellstart

Für den bequemen Start gibt es das Bootstrap-Skript `start.sh`, das alles in
einem Kommando erledigt:

```bash
./start.sh
```

Das Skript ist idempotent und übernimmt automatisch:

- **venv:** Fehlt `venv/`, wird sie mit einem gefundenen System-Python (>= 3.9)
  angelegt. Findet sich kein passendes Python, bricht das Skript mit klarer
  Meldung ab.
- **Abhängigkeiten:** werden nur installiert, wenn `import flask` fehlschlägt
  (oder mit `--reinstall` erzwungen) — via `pip install -r requirements.txt`.
- **`.env`:** Fehlt sie, wird sie aus `.env.example` kopiert (mit Hinweis auf die
  einzutragenden Zugangsdaten). Eine vorhandene `.env` wird **nie** überschrieben.
- **Browser:** öffnet nach kurzer Verzögerung `http://127.0.0.1:5000` (ausschaltbar
  mit `--no-browser`). Ein fehlender oder fehlschlagender Opener bricht den Start
  nicht ab — die URL wird dann nur ausgegeben.
- **Server:** startet anschließend `wsgi.py`; Beenden mit `Ctrl-C`.

Optionen:

| Flag           | Wirkung                                                    |
| -------------- | ---------------------------------------------------------- |
| `--no-browser` | Server starten, aber keinen Browser öffnen.                |
| `--reinstall`  | Abhängigkeiten aus `requirements.txt` neu installieren.    |
| `-h`, `--help` | Usage anzeigen und beenden (Exit 0).                       |

Ein unbekanntes Flag führt zu einer Fehlermeldung samt Usage und Exit-Code 2.

Optional lassen sich `HOST` und `PORT` als Umgebungsvariablen setzen; sie wirken
jedoch nur auf die angezeigte URL. Der tatsächliche Server-Port ist in `wsgi.py`
fest auf `127.0.0.1:5000` gesetzt.

> **Windows:** `start.sh` über **Git Bash** ausführen (nicht PowerShell oder
> cmd) — sonst wird der Shebang nicht korrekt interpretiert.

## Nutzung

1. Sicherstellen, dass `BACKUP_BASE_DIR` und die WebDAV-Zugangsdaten gesetzt sind.
2. Startseite öffnen — die direkten Unterordner werden als Checkboxen gelistet.
3. Optional „Verbindung testen".
4. Ordner auswählen und „Backup starten" — die Ergebnisseite zeigt Zähler und
   etwaige Fehler.

## Projektstruktur

```
.
├── app/
│   ├── __init__.py          # create_app-Factory (Blueprint-Registrierung)
│   ├── config.py            # Config aus Umgebungsvariablen (ohne Flask)
│   ├── webdav_client.py     # Wrapper um webdav3.client.Client
│   ├── backup.py            # Kernlogik: Einsammeln + Upload (ohne Flask)
│   ├── directory_service.py # Auflisten + Path-Traversal-Schutz (ohne Flask)
│   ├── routes.py            # Flask-Blueprint (GET /, POST /backup, /test-connection)
│   ├── templates/           # base.html, index.html, result.html
│   └── static/style.css     # schlichtes CSS ohne Framework
├── tests/                   # pytest-Suite inkl. conftest.py-Fixtures
├── wsgi.py                  # Entry-Point (load_dotenv + create_app)
├── start.sh                 # Bootstrap-Startskript (venv, Deps, .env, Server)
├── requirements.txt
├── pyproject.toml           # pytest-/coverage-Konfiguration (fail_under=80)
├── .env.example
└── .gitignore
```

## Tests

```bash
pytest --cov
```

Das Coverage-Gate ist auf `fail_under = 80` gesetzt; die Suite erreicht aktuell
rund 99 % Zeilenabdeckung. Es wird kein echter WebDAV-Server benötigt — der
Client wird in den Tests durch Fakes/Mocks ersetzt.

Hinweis: Die Tests schreiben ihre temporären Dateien in ein projektlokales
`.pytest_tmp/` (konfiguriert in `pyproject.toml`, per `.gitignore` ignoriert),
damit `tmp_path`-Fixtures unabhängig vom systemweiten Temp-Verzeichnis
funktionieren. Der Symlink-Test wird unter Windows übersprungen, da das Anlegen
von Symlinks dort erhöhte Rechte erfordert.

## Sicherheitshinweise

- Zugangsdaten kommen ausschließlich aus `.env`/Umgebung; nur `.env.example`
  wird eingecheckt. Passwörter werden nie gerendert, geloggt oder in
  Flash-/Fehlermeldungen aufgenommen.
- Path-Traversal-Schutz: Auswahlnamen müssen einfache, direkte Kindordner des
  Basisverzeichnisses sein. `..`, Pfadtrenner, absolute Pfade und heraus­führende
  Symlinks werden abgelehnt (`Path.resolve()` + `is_relative_to`).
- `WEBDAV_VERIFY_SSL` ist standardmäßig `true`. Ein Deaktivieren nur für
  vertrauenswürdige lokale Testserver.
- Es werden keine Stacktraces an Nutzer ausgegeben; `debug=False`.

## Bekannte Grenzen

- Nur Upload/Backup, kein Restore.
- Kein Inkremental- oder Deduplizierungs-Mechanismus — jede Datei wird bei jedem
  Lauf hochgeladen.
- Keine Authentifizierung der Web-UI; für lokalen Einzelplatzbetrieb gedacht.
