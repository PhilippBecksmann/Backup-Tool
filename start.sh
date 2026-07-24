#!/usr/bin/env bash
#
# start.sh — Ein-Kommando-Bootstrap fuer das WebDAV-Backup-Tool.
#
# Legt bei Bedarf eine virtuelle Umgebung an, installiert Abhaengigkeiten,
# erzeugt eine .env aus der Vorlage, oeffnet optional den Browser und startet
# den Flask-Server (wsgi.py).
#
# Nutzung:  ./start.sh [--no-browser] [--reinstall] [--help]
# Hinweis:  Unter Windows ueber Git Bash ausfuehren (nicht PowerShell/cmd).

set -euo pipefail

# Immer aus dem Skriptverzeichnis heraus arbeiten (robust bei Leerzeichen).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$SCRIPT_DIR" || exit 1

# --- Argument-Parsing --------------------------------------------------------
OPEN_BROWSER=1
REINSTALL=0

usage() {
  cat <<'EOF'
Verwendung: ./start.sh [OPTIONEN]

Startet das WebDAV-Backup-Tool mit einem einzigen Kommando. Legt bei Bedarf die
virtuelle Umgebung an, installiert Abhaengigkeiten, erzeugt .env aus der Vorlage
und startet den Server auf http://127.0.0.1:5000.

Optionen:
  --no-browser   Server starten, aber keinen Browser oeffnen.
  --reinstall    Abhaengigkeiten aus requirements.txt neu installieren.
  -h, --help     Diese Hilfe anzeigen und beenden.

Umgebungsvariablen (optional):
  HOST, PORT     Wirken nur auf die angezeigte URL. Der tatsaechliche Server-
                 Port ist in wsgi.py fest auf 127.0.0.1:5000 gesetzt.

Hinweis (Windows): Ueber Git Bash ausfuehren, nicht ueber PowerShell/cmd.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --no-browser) OPEN_BROWSER=0 ;;
    --reinstall)  REINSTALL=1 ;;
    -h|--help)    usage; exit 0 ;;
    *)
      echo "Unbekannte Option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

# --- OS-Erkennung ------------------------------------------------------------
os_name="$(uname -s)"
case "$os_name" in
  MINGW*|MSYS*|CYGWIN*) OS_FAMILY="windows" ;;
  Darwin)               OS_FAMILY="macos" ;;
  Linux)                OS_FAMILY="linux" ;;
  *)                    OS_FAMILY="unknown" ;;
esac

# --- System-Python finden (nur fuer venv-Erstellung) -------------------------
find_system_python() {
  local cand
  for cand in "python3" "python" "py -3" "py"; do
    if command -v "${cand%% *}" >/dev/null 2>&1; then
      if $cand -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 9) else 1)' >/dev/null 2>&1; then
        printf '%s\n' "$cand"
        return 0
      fi
    fi
  done
  return 1
}

if [ ! -d "venv" ]; then
  echo "Erstelle virtuelle Umgebung (venv/) ..."
  if ! SYS_PY="$(find_system_python)"; then
    echo "Fehler: Kein passendes Python (>=3.9) gefunden." >&2
    echo "Bitte Python 3.9+ installieren und erneut versuchen." >&2
    exit 1
  fi
  # SYS_PY kann mehrwortig sein (z. B. "py -3") und darf daher nicht gequotet werden.
  # shellcheck disable=SC2086
  $SYS_PY -m venv venv
fi

# --- venv-Python ueber Dateiexistenz aufloesen -------------------------------
if [ -x "venv/Scripts/python.exe" ]; then
  VENV_PY="venv/Scripts/python.exe"
elif [ -x "venv/bin/python" ]; then
  VENV_PY="venv/bin/python"
elif [ -f "venv/Scripts/python.exe" ]; then
  # Unter Git Bash ist das x-Bit fuer .exe unzuverlaessig — Existenz genuegt.
  VENV_PY="venv/Scripts/python.exe"
else
  echo "Fehler: venv-Python nicht gefunden (weder venv/Scripts/python.exe noch venv/bin/python)." >&2
  exit 1
fi

# --- Dependency-Gate ---------------------------------------------------------
need_install=0
if [ "$REINSTALL" -eq 1 ]; then
  need_install=1
elif ! "$VENV_PY" -c "import flask" >/dev/null 2>&1; then
  need_install=1
fi

if [ "$need_install" -eq 1 ]; then
  echo "Installiere Abhaengigkeiten aus requirements.txt ..."
  "$VENV_PY" -m pip install --upgrade pip >/dev/null
  "$VENV_PY" -m pip install -r requirements.txt
fi

# --- .env bereitstellen (vorhandene .env nie ueberschreiben) -----------------
if [ ! -f ".env" ]; then
  if [ -f ".env.example" ]; then
    cp ".env.example" ".env"
    echo "Hinweis: .env aus .env.example erzeugt. Bitte Zugangsdaten in .env eintragen."
    echo "         (WEBDAV_HOSTNAME, WEBDAV_LOGIN, WEBDAV_PASSWORD, BACKUP_BASE_DIR)"
  else
    echo "Warnung: Weder .env noch .env.example vorhanden — App startet mit Defaults." >&2
  fi
fi

# --- Git pre-commit Hook aktivieren (Tests vor jedem Commit) ------------------
# Setzt core.hooksPath auf .githooks, sodass der versionierte pre-commit-Hook
# ohne manuelle Kopie nach .git/hooks aktiv wird. Nur, wenn wir in einem Git-
# Repo sind und der Hook existiert; Fehler brechen den Start nie ab.
if [ -f ".githooks/pre-commit" ] && command -v git >/dev/null 2>&1; then
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    current_hooks_path="$(git config --get core.hooksPath || true)"
    if [ "$current_hooks_path" != ".githooks" ]; then
      git config core.hooksPath .githooks && \
        echo "Hinweis: Git pre-commit-Hook aktiviert (core.hooksPath=.githooks)."
    fi
  fi
fi

# --- HOST/PORT + URL ---------------------------------------------------------
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-5000}"
if [ "$HOST" != "127.0.0.1" ] || [ "$PORT" != "5000" ]; then
  echo "Warnung: wsgi.py bindet fest 127.0.0.1:5000. HOST/PORT wirken nur auf die" >&2
  echo "         angezeigte URL, nicht auf den tatsaechlichen Server-Port." >&2
fi
URL="http://${HOST}:${PORT}"

# --- Browser-Opener (bricht nie ab) ------------------------------------------
open_browser() {
  local url="$1"
  case "$OS_FAMILY" in
    windows)
      if command -v cmd.exe >/dev/null 2>&1; then
        cmd.exe //c start "" "$url" >/dev/null 2>&1 && return 0
      fi
      if command -v powershell.exe >/dev/null 2>&1; then
        powershell.exe -NoProfile -Command "Start-Process '$url'" >/dev/null 2>&1 && return 0
      fi
      ;;
    macos)
      if command -v open >/dev/null 2>&1; then
        open "$url" >/dev/null 2>&1 && return 0
      fi
      ;;
    linux)
      if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$url" >/dev/null 2>&1 && return 0
      fi
      ;;
  esac
  echo "Bitte oeffne im Browser: $url"
  return 0
}

# --- Server starten ----------------------------------------------------------
echo "Starte Server auf ${URL} (Ctrl-C zum Beenden) ..."
if [ "$OPEN_BROWSER" -eq 1 ]; then
  # Browser-Job MUSS vor exec starten (exec ersetzt die Shell).
  ( sleep 2; open_browser "$URL" || true ) &
  disown 2>/dev/null || true
fi
exec "$VENV_PY" wsgi.py
