<div align="center">

![PalworldSaveTools Logo](../assets/branding/PalworldSaveTools_Blue.png)

# PalworldSaveTools

**Ein umfassendes Toolkit zur Bearbeitung gespeicherter Dateien für Palworld**

[![Downloads](https://img.shields.io/github/downloads/deafdudecomputers/PalworldSaveTools/total)](https://github.com/deafdudecomputers/PalworldTools/releases/latest)
[![License](https://img.shields.io/github/license/deafdudecomputers/PalworldSaveTools)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-Join_for_support-blue)](https://discord.gg/sYcZwcT4cT)
[![NexusMods](https://img.shields.io/badge/NexusMods-Download-orange)](https://www.nexusmods.com/palworld/mods/3190)

[English](../../README.md) | [简体中文](README.zh_CN.md) | [Deutsch](README.de_DE.md) | [Español](README.es_ES.md) | [Français](README.fr_FR.md) | [Русский](README.ru_RU.md) | [日本語](README.ja_JP.md) | [한국어](README.ko_KR.md) | [Português (Brasil)](README.pt_BR.md) | [Português (Portugal)](README.pt_PT.md)

---

### **Laden Sie die Standalone-Version von [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest)** herunter

---

</div>
<div align="center">

## Übersicht

<img src="https://readme-typing-svg.demolab.com?lines=Was+genau+ist+das+f%C3%BCr+ein+Ding%3F;Dein+Save%2C+dein+Weg;Ein+Werkzeug%2C+um+sie+alle+zu+beherrschen&center=true&width=490&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Palworld Save Tools (PST) ist eine schnelle All-in-One-Desktopanwendung zum Überprüfen und Bearbeiten von Palworld-Sicherungsdateien. Es wurde mit Python und PySide6 erstellt und liest und schreibt das komprimierte Speicherformat des Spiels direkt – keine Spielmodifikationen erforderlich.

Ganz gleich, ob Sie einen dedizierten Server verwalten, zwischen Co-op- und dedizierten Servern migrieren, aufgegebene Daten bereinigen oder einzelne Pals optimieren müssen, PST bietet für alles eine einzige einheitliche Schnittstelle.

### Highlights

- **Plattformübergreifend** – Vorgefertigte Binärdateien für **Windows**, **Linux** und **macOS**.
- **Schnelles natives Parsen** – Einer der schnellsten verfügbaren Lesegeräte für gespeicherte Dateien, angetrieben von der [`palsav`](src/palsav)-Engine.
- **Visuelle Karte** – Interaktive Weltkarte mit Basis-/Spielermarkierungen, Sperrzonen und Koordinatenkalibrierung.
- **Umfassende Pal-Bearbeitung** – Volle Kontrolle über Statistiken, IVs, Seelen, Fähigkeiten, passives, Arbeitseignungen, Rang und Aussehensflaggen.
- **Tools auf Serverniveau** – Massenlöschung, Bereinigung, Konvertierung und Zeichenübertragung für Administratoren.
- **Automatische Backups** – Bei jedem Speichervorgang wird vor dem Schreiben ein Backup erstellt.
- **9 Sprachen** – Lokalisierte Benutzeroberfläche, In-App-Anleitungen und Dokumentation.





---





## Inhaltsverzeichnis

- [Übersicht](#übersicht)
- [Funktionen](#funktionen)
- [Installation](#installation)
- [Schnellstart](#schnellstart)
- [Anleitungen](#anleitungen)
- [Fehlerbehebung](#fehlerbehebung)
- [Aufbau aus der Quelle](#aufbau-aus-der-quelle)
- [Mitwirken](#mitwirken)
- [Lizenz](#lizenz)
- [Das Palworld-Team](#das-palworld-team)





---




<div align="center">

## Funktionen

<img src="https://readme-typing-svg.demolab.com?lines=Die+guten+Sachen;Schauen+Sie+es+sich+an;Vollgepackt+mit+Werkzeugen&center=true&width=290&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

| Kategorie | Was Sie tun können |
|---|---|
| **Spielerverwaltung** | Bearbeiten Sie Namen, Level, Statistiken und Technologiepunkte. Massenverwaltung von Gegenständen, pals, Technologie für alle Spieler. Bereinigen Sie inaktive oder doppelte Spieler. |
| **Pal Editor** | Ändern Sie Statistiken, IVs, Seelen, Rang, Fähigkeiten, passives, Arbeitseignung, Boss-/Glücksflaggen. Export/Import pals. Erkennen und beheben Sie illegale pals. Cheat-Modus für unbegrenztes Bearbeiten. |
| **Gildenverwaltung** | Gilden umbenennen, Anführer wechseln, Level festlegen. Schalten Sie Laborforschung frei. Verschiebe Spieler zwischen Gilden. Leere oder inaktive Gilden löschen. |
| **Basislager-Werkzeuge** | Alle Basen mit Gildeninformationen anzeigen. Blaupausen exportieren/importieren. Klonen Sie Basen für andere Gilden. Positionieren Sie die Basen auf der Karte neu. Radius anpassen. Inaktive Basen löschen. |
| **Kartenbetrachter** | Interaktive Weltkarte mit Basis- und Spielermarkierungen. Zeichnen Sie Sperrzonen ein. Kalibrierungsmodus. Weltkarten- und Baumkartenansichten. Zoomen, schwenken, anfliegen. |
| **Bestandsverwaltung** | Bearbeiten Sie Spielergegenstände, Schlüsselgegenstände und Ausrüstungsplätze. Schalte alle Schnellreisepunkte frei. Durchsuchen und bearbeiten Sie Basisinventare und Container aller Gilden. Basisarbeiter pals verwalten. |
| **Ausschlüsse** | Schützen Sie Spieler, Gilden und Stützpunkte mit dauerhaften Ausschlusslisten vor Säuberungen. Fügen Sie Einträge aus Kontextmenüs hinzu. |
| **Tools speichern** | Konvertieren Sie Speicherungen zwischen SAV und JSON. Konvertieren Sie GamePass in Steam. Übertragen Sie Charaktere zwischen Welten. Host-Speicherungen beheben. Kartenfortschritt wiederherstellen. Erweitern Sie die Palbox-Slots. |
| **Bereinigung & Dienstprogramme** | Löschen Sie leere Gilden, inaktive Basen/Spieler und nicht referenzierte Daten. Entfernen Sie ungültige Elemente/pals/strukturen. Dungeons, Bohrinsel, Versorgungslieferungen zurücksetzen. Zeitstempel korrigieren. |

### Spielerverwaltung

- Alle Spieler nach Name, Level, pal-Anzahl, UID, Gilde und zuletzt gesehener Zeit anzeigen und durchsuchen.
- Bearbeiten Sie Spielernamen, Level, Statistiken und Technologiepunkte.
- **Registerkarte „Statistik“** – Heldenstatistiken (Gesundheit, Ausdauer, Angriff, Verteidigung, Arbeitsgeschwindigkeit, Gewicht) mit korrekten, im Spiel berechneten Werten; Reliktfähigkeiten mit Schaltern und Spinnern.
- **Alle Statistiken maximieren** – Begrenzen Sie alle Statistiken sofort auf das Maximum (50 Punkte).
- **Massenoperationen** für mehrere Spieler: Gegenstandsverwaltung, pal-Verwaltung und Technologie-Freischaltungen.
- Inaktive Spieler nach Zeitschwelle löschen; Duplikate entfernen.

### Pal Editor

Eine umfassende Bearbeitungsoberfläche für jedes Pal, das einem beliebigen Spieler gehört. Pals werden von **Party** (aktive Truppe) und **Palbox** (Lagerung) organisiert.

- **Statistiken & IVs** – HP, Angriff, Verteidigung (IV 0–100), Level (1–80), Vertrauensrang (0–10).
- **Seelen** – HP, Angriff, Verteidigung, Handwerksgeschwindigkeit (0–20).
- **Fertigkeiten** – Aktive Fertigkeitsauswahl; lerne alle Bewegungen; Fähigkeiten zur Massensynchronisierung in Pals.
- **Passive Eigenschaften** – Passiver Picker mit vollständigen Spieldaten.
- **Arbeitseignung** – Legen Sie individuelle Arbeitseignungsstufen fest (0–10).
- **Aussehensflaggen** – Boss/Alpha, Lucky/Shiny, Predator, Awakened und Imported/DNA umschalten.
- **Rang & Sperre** – Rang und bevorzugte Sperrstufe festlegen (0–3).
- **Cheat-Modus** – Umschalten, um alle Obergrenzen zu erweitern: Level, IVs, Seelen, Kondensatorrang auf 255; Schalten Sie unbegrenzte Aktiv-/Passivfähigkeiten frei, wobei Duplikate zulässig sind.
- **Exportieren/Importieren** – Klicken Sie mit der rechten Maustaste auf einen beliebigen pal, um ihn als `.pstpal` (komprimiert) oder `.json` zu exportieren. Importieren Sie in leere Slots über Gruppen-, Palbox-, DPS- oder Basisarbeiter hinweg. Funktioniert für alle Spielstände und Spieler.
- **Max. Alle Pals** – Max. aller Statistiken (IVs, Seelen, Rang, Level) für alle pals in der Gruppe, alle Palbox-Seiten oder alle Basisarbeiter – berücksichtigt die Obergrenzen für den Cheat-Modus.
- **Illegales Pals beheben** – pals mit illegalen Statistiken, Fertigkeiten oder Eigenschaften pro Spieler erkennen und begrenzen.
- **Massenklonen/Löschen** – Artenauswahldialog mit Mengensteuerung und Quellenumschaltung (Party/Palbox/DPS) für Stapelvorgänge.
- Neuen Pals hinzufügen oder per Doppelklick schnell löschen.

### Gildenverwaltung

Zweiteilige Ansicht: Gildenliste oben, Mitgliederliste unten.

- Gilden umbenennen, Anführer wechseln, Gildenstufe festlegen, maximale Gildenstufe festlegen.
- Schalten Sie alle Laborforschungen frei; Alle Gilden neu aufbauen.
- Spieler zwischen Gilden verschieben; Leere oder inaktive Gilden löschen.

### Basislager-Werkzeuge

- Alle Basislager mit Gildenzugehörigkeit anzeigen.
- Basis-Blaupausen **Exportieren** nach `.json`; **Importieren** (einzelne oder mehrere Dateien) in jede Gilde.
- **Klonen** Basen für andere Gilden mit versetzter Positionierung.
- **Koordinaten ändern** – Klicken Sie mit der rechten Maustaste auf eine Basismarkierung auf der Karte, wählen Sie „Koordinaten ändern“ und klicken Sie dann auf eine beliebige Stelle, um die Basis zu teleportieren.
- **Base Nudge** – Verschieben Sie eine Basis um exakte X/Y/Z-Versatze, um Bodenbeschneidungen oder -schweben zu beheben.
- **Basisradius anpassen** (50 %–1000 %).
- Löschen Sie inaktive Basen und Nicht-Basiskartenobjekte.

### Kartenbetrachter

Interaktive Visualisierung Ihrer gesamten Welt.

- Basismarker (Haussymbol) und Spielermarker (Personensymbol) mit Detailfeldern.
- Überlagerungen umschalten: Basen, Spieler, Radiusringe, Sperrzonen.
- **Zonenzeichnung** – Zeichnen Sie rechteckige oder polygonale Sperrzonen direkt auf der Karte.
- **Kalibrierungsmodus** – Richten Sie die Karte genau an den Spielkoordinaten aus.
- Weltkarten- und Baumkartenansichten; Filtern Sie nach Gilde oder Spielername.
- Zoomen (1,0x–30,0x), Schwenken, Doppelklick, um zu einer Markierung zu fliegen.
- Rechtsklick-Markierungen und leerer Bereich für Verwaltungsaktionen.

### Bestandsverwaltung

**Spielerinventar** – Drei Unterregisterkarten:
- *Inventar* – Alle Gegenstände und Ausrüstung in der Haupttasche; Menge bearbeiten, hinzufügen, entfernen.
- *Schlüsselgegenstände* – Questgegenstände, Bildnisse und Technologie; Fügen Sie alle Bildnisse/Schlüsselelemente in großen Mengen hinzu.
- *Statistiken* – Level, HP, Ausdauer, Angriff, Verteidigung, Arbeitsgeschwindigkeit, Gewicht.
- Ausrüstungstafel für Waffen, Zubehör, Nahrung, Rüstung, Schild, Gleiter und Modulplätze.
- Schalten Sie alle Karten- und Schnellreisepunkte mit einem Klick frei.

**Basisinventar** – Durchsuchen und verwalten Sie Artikel und arbeiten Sie Pals über alle Basen hinweg:
- Elemente in Containern anzeigen/bearbeiten; durchsichtige Behälter; Containerplätze ändern.
- Gildenübergreifende Gegenstandsoperationen (Gegenstände in allen Gilden finden/entfernen).
- Gildenübergreifende Strukturlöschung.
- Unterregisterkarte **Basis Pals** – Verwalten Sie die jeder Basis zugewiesenen Arbeits-Pals mit vollständigen pal-Editor-Kontextmenüs.

### Ausschlüsse

Schutzlisten, die Spieler, Gilden und Stützpunkte vor Aufräumarbeiten schützen.

- Drei nebeneinander liegende Felder: ausgeschlossene Spieler-UIDs, Gilden-IDs und Basis-IDs.
- Fügen Sie Einträge über Rechtsklick-Kontextmenüs in den Registerkarten „Spieler“, „Gilden“ oder „Basen“ hinzu.
- Ausschlusslisten dauerhaft speichern und laden.
- Erstellen Sie Ihre Liste **bevor** Sie die Massenbereinigung durchführen.

### Werkzeuge speichern

Über die Registerkarte **Tools** als anklickbare Karten zugänglich:

| Werkzeug | Beschreibung |
|------|-------------|
| **Gespeicherte Dateien konvertieren** | Konvertieren zwischen SAV- und JSON-Format |
| **Konvertieren Sie GamePass → Steam** | Konvertieren Sie Xbox/GamePass-Speicherungen in das Steam-Format |
| **Konvertieren SteamID** | Konvertieren Sie Steam-IDs in Palworld-UIDs |
| **Karte wiederherstellen** | Vollständig freigeschalteten Kartenfortschritt auf alle Welten/Server anwenden |
| **Schlitzinjektor** | Palbox-Slots pro Spieler erhöhen |
| **Ändern Speichern** | Rohspeicherdaten öffnen und ändern |
| **Charakterübertragung** | Charaktere zwischen verschiedenen Welten/Servern übertragen (Cross-Save) |
| **Host-Speicherung beheben** | UIDs zwischen zwei Spielern austauschen (Host-Swap, Plattformmigration) |

### Bereinigungs- und Hilfsfunktionen

Diese Server-Vorgänge sind über **Menü → Funktionen** zugänglich und umfassen:

- **Löschen** – Leere Gilden, inaktive Basen/Spieler, doppelte Spieler, nicht referenzierte Daten löschen.
- **Bereinigung** – Entfernen Sie ungültige/modifizierte Elemente, ungültige pals und passives, ungültige Strukturen; unzulässiges pals beheben (Grenze auf zulässiges Maximum); Luftabwehrtürme zurücksetzen; entsperren private chests; alle Strukturen reparieren.
- **Zurücksetzen** – Missionen, Dungeons, Bohrinsel, Eindringling, Versorgungslieferungen zurücksetzen.
- **Zeitstempel** – Negative Zeitstempel korrigieren; Spielerzeiten zurücksetzen.
- **PalDefender** – `killnearestbase`-Befehle generieren.





---




<div align="center">

## Installation

<img src="https://readme-typing-svg.demolab.com?lines=Bringen+Sie+es+in+wenigen+Minuten+zum+Laufen;Herunterladen+und+loslegen;Keine+Einrichtung+erforderlich&center=true&width=420&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### Eigenständige Builds (empfohlen)

Vorgefertigte Binärdateien sind für alle drei Hauptplattformen ab [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest) verfügbar:

| Plattform | Herunterladen | Anforderungen |
|----------|----------|--------------|
| **Windows** | `PalworldSaveTools-*.exe` | Windows 10/11, [VC++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) (2015–2022) |
| **Linux** | `PalworldSaveTools-*-linux` | Jede moderne Distribution |
| **macOS** | `PalworldSaveTools-*-macos.dmg` | macOS 12+ (Monterey oder höher) |

Auch erhältlich für [Nexus Mods](https://www.nexusmods.com/palworld/mods/3190).

1. Laden Sie den passenden Build für Ihre Plattform herunter.
2. Extrahieren Sie die ausführbare Datei (falls archiviert) und führen Sie sie aus.
3. Das war's – kein Python oder Abhängigkeiten erforderlich.

> **Windows:** Wenn die Meldung „VCRUNTIME140.dll wurde nicht gefunden“ angezeigt wird, installieren Sie [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170).

> **Linux:** Möglicherweise müssen Sie die Datei als ausführbar markieren: `chmod +x PalworldSaveTools-*-linux`

> **macOS:** Wenn Gatekeeper die App blockiert, klicken Sie beim ersten Mal mit der rechten Maustaste → **Öffnen** oder führen Sie `xattr -d com.apple.quarantine /path/to/app` aus.

### Aus der Quelle (Alle Plattformen)

PST verwendet [`uv`](https://docs.astral.sh/uv/) für die Abhängigkeitsverwaltung. Das Startskript erstellt automatisch eine virtuelle Umgebung und installiert alles.

**Voraussetzungen:** [Python 3.11+](https://www.python.org/) und [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
uv run start.py
```

**Windows** (Doppelklick-Launcher):
```
start.cmd
```

Der Launcher erstellt einen `.venv`, installiert Abhängigkeiten über `uv sync` und startet die App. Es bereinigt die Sperrdatei beim Beenden, sodass jeder Lauf reproduzierbar ist.





---




<div align="center">

## Schnellstart

<img src="https://readme-typing-svg.demolab.com?lines=Laden.+Bearbeiten.+Speichern.+So+einfach.;Drei+Schritte+zum+Ruhm;So+einfach+ist+das&center=true&width=450&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

1. **Laden Sie Ihren Speicherstand**
   - Klicken Sie auf **Menü → Laden und Speichern** oder ziehen Sie eine `.sav`-Datei per Drag-and-Drop in das Fenster.
   - Navigieren Sie zu Ihrem Palworld-Speicherordner und wählen Sie `Level.sav`.

2. **Erkunden Sie Ihre Daten**
   - Verwenden Sie die Registerkarten – **Karte**, **Tools**, **Spieler**, **Gilden**, **Basen**, **Spielerinventar**, **Basisinventar**, **Pal Editor**, **Ausschlüsse** – um Ihren Speicherstand zu erkunden.
   - Die Statistikleiste zeigt Live-Zählungen; Schnellnavigationssymbole springen zu den einzelnen Abschnitten.

3. **Änderungen vornehmen**
   - Zum Auswählen mit der linken Maustaste klicken; Klicken Sie mit der rechten Maustaste auf fast alles, um kontextbezogene Aktionen auszuführen.
   - Doppelklicken Sie, um schnell zu bearbeiten oder schnell zu löschen (weitere Informationen finden Sie in den In-App-Anleitungen).

4. **Speichern Sie Ihre Änderungen**
   - Klicken Sie auf **Menü → Änderungen speichern**. Backups werden automatisch erstellt.

> **Tipp:** Jede Registerkarte verfügt über eine integrierte Anleitung – klicken Sie auf das Hilfesymbol in einer beliebigen Registerkarte, um genau zu sehen, was sie tun kann. Um tiefere Informationen zu erhalten, **bewegen Sie den Mauszeiger über eine beliebige Schaltfläche, ein Feld oder ein Steuerelement**, um detaillierte Tooltips in der Kopfzeile anzuzeigen. Das In-App-Tooltip-Hilfesystem ist Ihre beste Referenz, um genau zu verstehen, was die einzelnen Funktionen bewirken und wie sie verwendet werden.





---




<div align="center">

## Anleitungen

<img src="https://readme-typing-svg.demolab.com?lines=Schritt-f%C3%BCr-Schritt-Anleitungen;Folgen+Sie+der+Anleitung;Wir+zeigen+Ihnen+wie&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### Dateispeicherorte speichern

**Host / Koop (Windows):**
```
%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\
```

**Dedizierter Server:**
```
steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\
```

### Kartenfreischaltung

PST kann die vollständige Karte (alle Schnellreisepunkte) für Ihren Speicherstand freischalten:

1. Laden Sie Ihren Speicherstand im PST-Format.
2. Öffnen Sie die Registerkarte **Spielerinventar** und klicken Sie auf **Alle Karten + Schnellreisen freischalten** für einen einzelnen Spieler, **oder**
3. Verwenden Sie das Tool **Karte wiederherstellen** auf der Registerkarte „Extras“, um den freigeschalteten Kartenfortschritt auf **allen** Ihren Welten/Servern gleichzeitig anzuwenden.
4. Änderungen speichern. Es werden automatische Backups erstellt.

### Koop → Dedizierter Server

<details>
<summary>Zum Erweitern klicken</summary>

Verschieben Sie Ihre Koop-Welt (die Sie von Ihrem PC aus hosten) auf einen dedizierten Server, damit andere auch dann spielen können, wenn Sie offline sind.

**So funktioniert es:** Koop-Speicherungen verwenden `0001.sav` für den Host-Spieler. Bei dedizierten Servern ist das nicht der Fall – jeder Spieler hat eine reguläre UID. Fix Host Save **tauscht** zwei Spielerdateien aus (wie beim Tauschen von Plätzen), keine Kopie. Dein Koop-Charakter in `0001.sav` wird in den Slot des Servers getauscht.

1. **Kopieren Sie Ihren Koop-Speicher auf den Server.**
   - Koop-Speicherort: `%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\`
   - Kopieren Sie `Level.sav` und den Ordner `Players` von dort.
   - In den Speicherordner des Servers einfügen: `steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\`

2. **Treten Sie dem Server bei und erstellen Sie einen temporären Charakter.**
   - Starten Sie den Server, treten Sie ihm bei und erstellen Sie einen neuen Charakter (beliebiger Name/Aussehen – dies ist nur ein Platzhalter).
   - Warten Sie auf eine automatische Speicherung und fahren Sie dann den Server herunter.

3. **Tausch deinen Koop-Charakter in den Server-Slot.**
   - Öffnen Sie PST → **Tools** → **Fix Host Save**.
   - Navigieren Sie zum `Level.sav` des Servers.
   - **Quellspieler**: Wählen Sie Ihren Koop-Charakter aus (den in `0001.sav` – aufgeführt als Host).
   - **Zielspieler**: Wählen Sie den temporären Charakter aus, den Sie gerade erstellt haben.
- Klicken Sie auf die Schaltfläche, um den Austausch durchzuführen.

4. **Starten Sie den Server.**
   - Ihr ursprünglicher Koop-Charakter (mit allen Fortschritten, Pals, Basen) ist jetzt mit dem Server verknüpft. Der temporäre Platzhalter ist verschwunden.

</details>

### Dedizierter Server → Koop

<details>
<summary>Zum Erweitern klicken</summary>

Bringen Sie Ihren dedizierten Server-Charakter zurück zu einem lokalen Koop-Speicher – nützlich, wenn Sie keinen Server mehr mieten oder offline spielen möchten.

**So funktioniert es:** Gleicher GUID-Austausch in umgekehrter Reihenfolge – Fix Host Save **tauscht** zwei Dateien aus, keine Kopie. Ihr Server-Charakter (reguläre UID) wird in `0001.sav` (den Host-Slot) verschoben, sodass Sie mit Ihrem Server-Fortschritt im Koop-Modus hosten können.

1. **Kopieren Sie Ihren Serverspeicher auf Ihren lokalen PC.**
   - Speicherort des Servers: `steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\`
   - Kopieren Sie `Level.sav` und den Ordner `Players` von dort.
   - In Ihren lokalen Koop-Ordner einfügen: `%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\`

2. **Hosten Sie ein Koop-Spiel und erstellen Sie einen temporären Charakter.**
   - Starten Sie Palworld, veranstalten Sie eine Koop-Sitzung und erstellen Sie einen neuen Charakter.
   - Lassen Sie es automatisch speichern und schließen Sie dann Palworld.

3. **Tausch deinen Server-Charakter in den Host-Slot.**
   - Öffnen Sie PST → **Tools** → **Fix Host Save**.
   - Navigieren Sie zur örtlichen Genossenschaft `Level.sav`.
   - **Quellspieler**: Wählen Sie Ihren dedizierten Servercharakter aus (aufgelistet nach seiner UID).
   - **Zielspieler**: Wählen Sie den temporären Koop-Charakter (den in `0001.sav` – aufgeführt als Host).
   - Klicken Sie auf die Schaltfläche, um den Austausch durchzuführen.

4. **Normalerweise Gastgeber-Koop.**
   - Ihr Servercharakter ist jetzt der Host (`0001.sav`). Alle Fortschritte, Pals und Basen intakt.

</details>

### Host wechseln (Koop-Tausch)

<details>
<summary>Zum Erweitern klicken</summary>

Zwei Spieler wollen den Gastgeber wechseln. Spieler A war Gastgeber – sein Charakter lebt in `0001.sav`. Spieler B tritt als Kunde bei – sein Charakter lebt in `1234.sav`. Jetzt möchten sie, dass Spieler B der Host wird, aber der Host-Slot ist immer `0001.sav`.

**Schlüsselkonzept – Fix Host Save tauscht immer zwei Spieler aus.** Es tauscht ihre Speicherdateien aus, als würden zwei Personen ihre Plätze tauschen. Es wird NICHT eins auf das andere kopiert. Nach jedem Austausch sind beide Player weiterhin vorhanden – sie befinden sich lediglich in unterschiedlichen Dateien.

Da ein Austausch Spieler B in den Host-Slot verschiebt, die Daten von Spieler A jedoch in der alten Datei von B verbleiben, ist ein zweiter Austausch erforderlich, um den ursprünglichen Charakter von Spieler A wiederherzustellen. So geht's:

---

**Ausgangszustand:**
```
0001.sav  = Player A (current host)
1234.sav  = Player B (current client)
```

---

**Schritt 1 – A und B vertauschen.**
- Öffnen Sie PST → **Tools** → **Fix Host Save**.
- Navigieren Sie zu Ihrer Genossenschaft `Level.sav`.
- **Quelle**: Spieler A (`0001.sav`). **Ziel**: Spieler B (`1234.sav`).
- Klicken Sie auf die Schaltfläche. Fix Host Save tauscht die beiden Dateien aus.

**Nach Schritt 1:**
```
0001.sav  = Player B  ← now the host with B's character
1234.sav  = Player A  ← A's data is here, but this UID no longer exists in the game
```

---

**Schritt 2 – Spieler B ist Gastgeber, Spieler A tritt bei.**
- Spieler B ist Gastgeber der Welt. Spieler A tritt bei.
- Da A nicht mehr der Host ist, weist Palworld dem temporären Charakter von A eine brandneue UID zu (z. B. `9999.sav`).
- Spieler A erreicht **Level 2** mit dem temporären Charakter, dann verlassen alle das Spiel.

**Nach Schritt 2:**
```
0001.sav  = Player B (host, correct)
1234.sav  = Player A's original data (not linked to any active UID)
9999.sav  = Player A's temporary character (fresh, Level 2+)
```

---

**Schritt 3 – Tauschen Sie die Originaldaten von A in die neue UID von A aus.**
- Öffnen Sie **Fix Host Save** erneut mit demselben `Level.sav`.
- **Quelle**: `1234.sav` (Originaldaten von Spieler A). **Ziel**: `9999.sav` (der temporäre Charakter von Spieler A).
- Klicken Sie auf die Schaltfläche. Sie tauschen erneut.

**Nach Schritt 3:**
```
0001.sav  = Player B (host, correct)
1234.sav  = Player A's temp character (unused, can delete)
9999.sav  = Player A's original character  ← restored!
```

---

**Fertig.** Spieler B hostet mit dem ursprünglichen Charakter von Spieler B. Spieler A schließt sich dem ursprünglichen Charakter von Spieler A an. Der übrig gebliebene `1234.sav` kann ignoriert oder gelöscht werden.

> **Warum zwei Swaps?** Fix Host Save **tauscht** zwei Dateien aus – es handelt sich nicht um eine Kopie. Durch den ersten Austausch wird B in den Host-Slot verschoben, aber die Daten von A landen in der alten UID von B (die im Spiel nicht mehr existiert). Der zweite Austausch verschiebt die Daten von A in die neue Client-UID von A. Zwei Swaps, alle Fortschritte bleiben erhalten.

</details>

### Charakterübertragung (Cross-Save)

<details>
<summary>Zum Erweitern klicken</summary>

Kopieren Sie einen Spieler (mit allen Pals, Inventar, Technologie und Fortschritt) von einer Welt in eine andere – nützlich, um Ihren Charakter zwischen einer Koop-Welt und einem dedizierten Server oder zwischen zwei Servern zu bewegen.

**So funktioniert es:** Im Gegensatz zu Fix Host Save (bei dem zwei Dateien **ausgetauscht** werden) **kopiert** die Charakterübertragung einen Spieler von einem `Level.sav` in ein anderes. Die Quellspeicherung bleibt unberührt.

1. Öffnen Sie PST → **Tools** → **Zeichenübertragung**.
2. **Laden Sie den Quellspeicher** – klicken Sie auf die Schaltfläche „Quelle“ und wählen Sie den `Level.sav` aus, der das Zeichen enthält, das Sie kopieren möchten (z. B. Ihr alter Server).
3. **Laden Sie den Zielspeicher** – klicken Sie auf die Schaltfläche „Ziel“ und wählen Sie den `Level.sav` aus, in den Sie kopieren möchten (z. B. Ihren neuen Server).
4. **Wählen Sie den zu übertragenden Spieler** aus der Liste der Quellspieler auf der linken Seite aus.
5. **Wählen Sie in der Liste „Zielspieler“ auf der rechten Seite aus, wo sie platziert werden sollen. Sie können einen vorhandenen Spieler überschreiben oder ihn für einen neuen Platz leer lassen.
6. Klicken Sie auf **Übertragen**. Der Charakter, Pals, das Inventar und die Gildenmitgliedschaft werden in den Zielspeicher kopiert.
7. Änderungen speichern. Es werden automatische Backups erstellt.

Sie können auch **alle Spieler** auf einmal übertragen, indem Sie auf die Schaltfläche „Alle übertragen“ klicken.

</details>

### Basisexport / Import / Klonen

<details>
<summary>Zum Erweitern klicken</summary>

**Eine Basis exportieren:**
1. Gehen Sie zur Registerkarte **Stützpunkte** (oder verwenden Sie den Map Viewer).
2. Klicken Sie mit der rechten Maustaste auf eine Basis → **Basis exportieren**.
3. Speichern Sie als `.json`-Blueprint-Datei.

**Eine Basis importieren:**
1. Klicken Sie mit der rechten Maustaste auf die Zielgilde (in der Registerkarte „Basen“, „Map Viewer“ oder „Gilden“).
2. Wählen Sie **Basis importieren** (einzelne Datei) oder **Basen importieren (mehrere Dateien)**.
3. Wählen Sie Ihre exportierte(n) `.json`-Datei(en) aus.

**Klonen einer Basis:**
1. Klicken Sie mit der rechten Maustaste auf eine Basis → **Basis klonen**.
2. Wählen Sie die Zielgilde aus.
3. Die Basis wird mit versetzter Positionierung geklont.

**Anpassen des Basisradius:**
1. Klicken Sie mit der rechten Maustaste auf eine Basis → **Radius anpassen**.
2. Geben Sie einen neuen Radius ein (50 %–1000 %).
3. Speichern Sie den Speicherstand im Spiel und laden Sie ihn erneut, damit die Strukturen neu zugewiesen werden können.

</details>





---




<div align="center">

## Fehlerbehebung

<img src="https://readme-typing-svg.demolab.com?lines=Wenn+die+Dinge+schiefgehen;Keine+Panik;Wir+haben+alles+gesehen&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### „VCRUNTIME140.dll wurde nicht gefunden“ (Windows)

Installieren Sie den [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) (2015–2022).

### `struct.error` beim Parsen eines Speicherstands

Das Speicherdateiformat ist veraltet. Laden Sie den Speicherstand im Spiel (Solo, Koop oder Dedizierter Server) einmal, um eine automatische Strukturaktualisierung auszulösen, und versuchen Sie es dann erneut. Stellen Sie sicher, dass der Speicherstand mit oder nach dem neuesten Spiel-Patch aktualisiert wurde.

### GamePass Konverter funktioniert nicht

1. Schließen Sie die GamePass-Version von Palworld vollständig.
2. Warten Sie einige Minuten, bis die Dateihandles freigegeben werden.
3. Führen Sie den Konverter GamePass → Steam aus.
4. Starten Sie Palworld zur Überprüfung auf GamePass.

### Linux/MacOS-Binärdatei wird nicht gestartet

- **Linux:** `chmod +x PalworldSaveTools-*-linux`, um es als ausführbar zu markieren.
- **macOS:** Wenn vom Gatekeeper blockiert, klicken Sie mit der rechten Maustaste → **Öffnen** oder führen Sie `xattr -d com.apple.quarantine /path/to/app` aus.





---




<div align="center">

## Aufbau aus der Quelle

<img src="https://readme-typing-svg.demolab.com?lines=Stellen+Sie+es+selbst+zusammen;Bauen+Sie+Ihr+eigenes;Von+der+Quelle+zur+Bin%C3%A4rdatei&center=true&width=340&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

PST unterstützt zwei Build-Pfade. Die CI/CD-Pipeline verwendet Nuitka für plattformübergreifende Release-Binärdateien; cx_Freeze wird für das lokale Windows-Installationsprogramm verwendet.

### Nuitka (Plattformübergreifend – Wird von CI/Releases verwendet)

Erfordert Python 3.11+ und `uv`. Nuitka wird automatisch installiert.

```bash
# One-file build (Windows / Linux)
uv run python build/nuitka/build_nuitka.py --onefile

# One-directory build (macOS .app)
uv run python build/nuitka/build_nuitka.py --onedir
```

Ausgaben gehen an `dist/`:
- Windows → `dist/PalworldSaveTools-*.exe`
- Linux → `dist/PalworldSaveTools-*-linux`
- macOS → `dist/PalworldSaveTools.app` → verpackt als `.dmg`

### cx_Freeze (Windows Installer)

Für ein lokales Windows `.zip`-Paket:

```
scripts\build_cx.cmd
```

Dadurch wird `PST_standalone_v{version}.zip` im Projektstamm erstellt.

### Interaktiver Builder

Ein interaktives Menü zur Auswahl eines Build-Modus:

```bash
uv run python build/build_interactively.py
```





---




<div align="center">

## Mitwirken

<img src="https://readme-typing-svg.demolab.com?lines=M%C3%B6chten+Sie+helfen%3F+Hier+erfahren+Sie%2C+wie;Treten+Sie+dem+Team+bei;Jeder+Beitrag+z%C3%A4hlt&center=true&width=440&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Beiträge sind willkommen! Bitte senden Sie gerne einen Pull Request.

1. Forken Sie das Repository.
2. Erstellen Sie Ihren Feature-Zweig (`git checkout -b feature/AmazingFeature`).
3. Übernehmen Sie Ihre Änderungen (`git commit -m 'Add some AmazingFeature'`).
4. Drücken Sie auf den Zweig (`git push origin feature/AmazingFeature`).
5. Öffnen Sie eine Pull-Anfrage.





---




<div align="center">

## Haftungsausschluss

<img src="https://readme-typing-svg.demolab.com?lines=Lesen+Sie+dies%2C+bevor+Sie+etwas+kaputt+machen;Sie+wurden+gewarnt;Zuerst+sichern%21;Mit+gro%C3%9Fer+Kraft...&center=true&width=520&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

**Die Verwendung dieses Tools erfolgt auf eigene Gefahr. Sichern Sie immer Ihre Sicherungsdateien, bevor Sie Änderungen vornehmen.**

Die Entwickler sind nicht verantwortlich für den Verlust gespeicherter Daten oder Probleme, die durch die Verwendung dieses Tools entstehen können.





---




<div align="center">

## Unterstützung

<img src="https://readme-typing-svg.demolab.com?lines=Wir+stehen+Ihnen+zur+Seite;Brauchen+Sie+Hilfe%3F;Wir+sind+f%C3%BCr+Sie+da&center=true&width=340&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

- **Discord:** [Join us for support, base builds, and more!](https://discord.gg/sYcZwcT4cT)
- **GitHub Probleme:** [Report a bug](https://github.com/deafdudecomputers/PalworldSaveTools/issues)
- **Nexus-Mods:** [Download & discuss](https://www.nexusmods.com/palworld/mods/3190)





---




<div align="center">

## Lizenz

<img src="https://readme-typing-svg.demolab.com?lines=MIT+%E2%80%93+machen+Sie%2C+was+Sie+wollen;Kostenlos+wie+beim+Bier;Open+Source%2C+offener+Geist&center=true&width=430&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Dieses Projekt ist unter der MIT-Lizenz lizenziert – Einzelheiten finden Sie in der Datei [license](license).





---




<div align="center">

## Das Palworld-Team

<img src="https://readme-typing-svg.demolab.com?lines=Die+Menschen+hinter+der+Magie;Lernen+Sie+das+Team+kennen;Mit+Leidenschaft+gebaut&center=true&width=420&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Ohne die Menschen dahinter gäbe es dieses Projekt nicht.

### Aktive Betreuer

**[Pylar](https://github.com/deafdudecomputers)** – Der Mann, mit dem alles begann. Jede Zeile dieses Tools geht auf seine Vision und seine unermüdliche Arbeit an der Speicher-Engine, der GUI und den Funktionen zurück, die Sie täglich verwenden.

**[cyrix](https://github.com/CyrixJD115)** – Refactorer und Sub-Maintainer. Konzentriert sich auf Codequalität, Vereinfachung und strukturelle Verbesserungen – so bleibt die Codebasis sauber, kleiner und einfacher zu warten, wenn das Projekt wächst.

### Mitwirkende

**[dkoz](https://github.com/dkoz)** – Der Mann hinter den Ausweisen. Bietet Spieldaten-IDs, strukturelle Einblicke in die ID-Codes und umfassende Kenntnisse darüber, wie die Daten von Palworld miteinander verknüpft sind, sodass das Tool bei jedem Spielupdate korrekt bleibt.

**[oMaN-Rod](https://github.com/oMaN-Rod)** – Stellte den ursprünglichen Speicherparser bereit, von dem dieses Projekt geforkt wurde. Ohne seine grundlegende Arbeit zum Knacken des Palworld-Speicherformats gäbe es das alles nicht. Der Fork hat seinen Parser zu dem optimiert und vereinfacht, was PST heute ist.
**[Okaetsu](https://github.com/Okaetsu)** – Modding-Erkenntnisse, die den Basisimport/-export ermöglichten. Sein Verständnis dafür, wie Palworld Basisdaten von der Modding-Seite aus strukturiert, überbrückte die Lücke zwischen Modding und Save Editing und machte dieses Feature Wirklichkeit.





---




<div align="center">

## Danksagungen

<img src="https://readme-typing-svg.demolab.com?lines=Wo+Kredit+f%C3%A4llig+ist;Vielen+Dank+euch+allen;Wir+stehen+auf+Schultern&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Ein großes Dankeschön an:

- **Palworld**, entwickelt von Pocketpair, Inc. – für das Spiel, das uns alle zusammengebracht hat.
- **Die Fehlerreporter** – jedes eingereichte Problem, jeder gefundene Randfall, jedes in Discord eingefügte Protokoll. Mit jedem Bericht machen Sie dieses Tool robuster.
- **Die Palworld-Modding-Community** – andere Modder, Tool-Entwickler und Tüftler, die Wissen teilen, Formate zurückentwickeln und das Ökosystem vorantreiben. Dieses Projekt steht auf den Schultern dieser gemeinsamen Anstrengung.
- **Alle Mitwirkenden und Community-Mitglieder** – egal, ob Sie eine PR eingereicht, eine Frage in Discord beantwortet oder einfach einem Freund von PST erzählt haben – vielen Dank.

---

<div align="center">

![Divider](../assets/branding/PalworldSaveTools_readme_divider.png)

**Hergestellt mit ❤️ für die Palworld-Community**

[⬆ Back to Top](#palworld-save-tools)

</div>