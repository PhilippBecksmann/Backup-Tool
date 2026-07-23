---
name: python-security-check
description: >
  Analysiert automatisch den gesamten Python-Code im aktuellen Projektverzeichnis und
  prüft ihn gegen Security-Best-Practices. Findet potenzielle Schwachstellen, priorisiert
  Risiken nach High/Medium/Low und liefert konkrete, umsetzbare Verbesserungsvorschläge.
  Als wiederkehrendes Security-Review-Werkzeug für Python-Projekte nutzbar. Einsetzen,
  wenn nach einem Sicherheitscheck, Security-Audit, Vulnerability-Scan oder Security-Review
  von Python-Code gefragt wird (Slash-Command /python-security-check).
---

# Python Security Check

Du führst ein statisches Security-Review des gesamten relevanten Python-Codebestands im
aktuellen Projektverzeichnis durch. Ziel: Schwachstellen finden, nach Risiko priorisieren
und pro Fund einen konkreten Fix vorschlagen. Du schreibst dabei **keinen** Produktivcode
und veränderst keine Dateien — du lieferst einen Report.

## Ablauf

### 1. Umfang bestimmen
- Ermittle alle relevanten `.py`-Dateien mit `Glob` (`**/*.py`).
- Schließe irrelevante Pfade aus: `venv/`, `.venv/`, `env/`, `site-packages/`,
  `__pycache__/`, `build/`, `dist/`, `.git/`, sowie generierte/vendored Bibliotheken.
- **Tests einbeziehen**, aber im Report als solche kennzeichnen (Fund in Testcode ist i. d. R.
  niedrigere Priorität als in Produktivcode).
- Nenne kurz, wie viele Dateien geprüft werden.

### 2. Analyse durchführen
Prüfe den Code gezielt gegen die folgenden Kategorien. Nutze `Grep` für schnelle
Muster-Suchen und `Read`, um Treffer im Kontext zu verifizieren. **Melde nur verifizierte
Funde** — kein Raten, keine reinen Vermutungen ohne Codestelle.

**Code Injection & Ausführung**
- `eval`, `exec`, `compile` auf nicht vertrauenswürdigen Eingaben
- `subprocess.*` / `os.system` / `os.popen` mit `shell=True` oder String-Interpolation
- `pickle`/`marshal`/`shelve`-Deserialisierung nicht vertrauenswürdiger Daten
- `yaml.load` ohne `SafeLoader`
- Dynamische Imports (`__import__`, `importlib`) aus Nutzereingaben

**Injection (SQL / Command / Template / Path)**
- SQL per String-Konkatenation/`f`-Strings statt parametrisierter Queries
- Path Traversal: Nutzereingaben in Dateipfaden ohne Normalisierung/Whitelist
- Template-Injection, fehlendes Autoescaping (`|safe`, `autoescape false`)
- Server-Side Request Forgery (SSRF): Nutzer-URLs an `requests`/`urllib` ohne Prüfung

**Secrets & Credentials**
- Hartkodierte Passwörter, API-Keys, Tokens, private Keys im Code
- Secrets in Logs, Fehlermeldungen oder Exceptions
- Committed `.env`/Config mit echten Credentials

**Kryptografie & Zufall**
- Schwache Hashes (`md5`, `sha1`) für Sicherheitszwecke, Passwörter ohne Salt/KDF
- `random` statt `secrets` für Tokens/Passwörter
- Deaktivierte TLS-Prüfung (`verify=False`, `ssl._create_unverified_context`)

**Web/Framework (Flask/Django/FastAPI)**
- `debug=True` in Produktion, fehlende `SECRET_KEY`-Härtung
- Fehlende Input-Validierung / Autorisierung an Endpunkten
- Unsichere CORS-, Cookie- oder Session-Konfiguration (`Secure`/`HttpOnly`/`SameSite`)
- Offene Redirects, fehlender CSRF-Schutz

**Sonstiges**
- Zu weite Exception-Behandlung, die Fehler verschluckt (`except: pass`)
- Unsichere Temp-Dateien (`tempfile.mktemp`), Race Conditions
- Veraltete/verwundbare Abhängigkeiten in `requirements.txt`/`pyproject.toml`
  (auffällige, bekannt unsichere Versionen benennen — ohne CVE-Datenbank raten zu wollen)
- Übermäßige Berechtigungen bei Datei-/Verzeichniserstellung

### 3. Risiko priorisieren
Ordne jeden Fund einer Stufe zu:
- **HIGH** — direkt ausnutzbar, ernste Auswirkung: RCE, Injection auf Nutzerpfad,
  offengelegte Secrets, deaktivierte TLS-Prüfung, unsichere Deserialisierung.
- **MEDIUM** — ausnutzbar unter Bedingungen oder mit spürbarer Auswirkung: schwache Krypto,
  fehlende Validierung, unsichere Konfiguration, Path-Traversal mit Teilschutz.
- **LOW** — Härtung/Defense-in-Depth: breite Excepts, kleinere Info-Leaks, Funde in Testcode,
  veraltete Muster ohne direkten Angriffspfad.

Bewerte nach realem Angriffspfad, nicht nur nach Musterfund. Erreicht eine Nutzereingabe die
Stelle nicht, stufe entsprechend herab und begründe es.

### 4. Report ausgeben
Gib einen strukturierten Markdown-Report auf Deutsch aus:

1. **Zusammenfassung** — Anzahl geprüfter Dateien, Funde je Stufe (z. B. `HIGH: 2, MEDIUM: 3, LOW: 4`),
   Gesamteinschätzung in 1–2 Sätzen.
2. **Funde** — nach Priorität sortiert (HIGH zuerst). Pro Fund:
   - **Titel** + Risikostufe
   - **Ort**: `pfad/datei.py:zeile` (klickbar)
   - **Problem**: was ist unsicher und warum (kurz, konkret)
   - **Angriffsszenario**: wie es ausgenutzt werden könnte
   - **Fix**: konkrete, umsetzbare Empfehlung — möglichst mit kurzem Codebeispiel
     der sicheren Variante
3. **Positiv-Befunde** (optional, kurz) — vorhandene gute Schutzmaßnahmen, damit klar wird,
   was bereits abgesichert ist.
4. **Empfohlene nächste Schritte** — priorisierte To-do-Liste; ggf. Hinweis auf Tools
   wie `bandit`, `pip-audit`, `safety` für automatisierte, wiederkehrende Läufe.

## Regeln
- **Nur Analyse, keine Änderungen.** Fixes werden vorgeschlagen, nicht angewendet, außer der
  Nutzer bittet ausdrücklich danach.
- **Keine False Positives durch blindes Grep** — jeden Treffer im Kontext lesen und verifizieren.
- **Nichts erfinden.** Keine Datei, Zeile oder Schwachstelle behaupten, die nicht belegt ist.
- Findet sich **nichts**, das klar sagen und die geprüften Kategorien auflisten — kein
  künstliches Aufblähen des Reports.
- Prägnant bleiben: die HIGH-Funde und der Fix sind das Wichtigste.
