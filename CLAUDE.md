# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Status

Dieses Projekt ist noch leer — es existieren bisher keine Quelldateien, keine
Build-Konfiguration und kein Git-Repository. Die folgenden Abschnitte sind
Platzhalter und sollten befuellt werden, sobald das Projekt Form annimmt.

Tipp: Sobald erste Dateien vorhanden sind, `/init` erneut ausfuehren — dann
kann eine fundierte, aus dem Code abgeleitete CLAUDE.md erzeugt werden.

## Commands

<!-- Build / Run / Test / Lint hier eintragen, sobald definiert.
     Beispiel:
     - Build:  ...
     - Test (alle):  ...
     - Test (einzeln):  ...
     - Lint:  ...
-->

## Architecture

<!-- High-Level-Architektur beschreiben, sobald Struktur existiert:
     - Einstiegspunkt(e)
     - Wichtigste Module und ihr Zusammenspiel
     - Datenfluss / zentrale Abstraktionen
-->

## Conventions

<!-- Projektspezifische Konventionen, die sich nicht aus dem Code ergeben. -->

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
  nach. Voraussetzung ist ein initialisiertes Git-Repository mit Remote (siehe Hinweis
  unten).
- Reine Nicht-Implementierungsaufgaben (Fragen beantworten, Doku lesen, Recherche ohne
  Codeänderung) benötigen die Pipeline nicht.

> Hinweis: Dieses Projekt hat aktuell **kein Git-Repository**. Bevor der Finalizer
> pushen kann, sind einmalig `git init`, ein erster Commit und ein konfigurierter
> Remote (`git remote add origin …`) nötig. Ohne Remote meldet der Finalizer den
> fehlenden Push, statt still fehlzuschlagen.
