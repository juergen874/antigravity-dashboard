# ⚡ Antigravity CLI • Mobile Web Dashboard

Ein extrem leichtgewichtiges, modernes und mobiles Web-Dashboard für die **Antigravity CLI** und Termux/Linux-Entwicklungsumgebungen.

---

## ✨ Features im Überblick

### 1. 🟢 Status-Leiste oben
- **Echtzeit-Verbindungsstatus:** Live-Indikator (Grün = Verbunden mit Ping-Latenz in Millisekunden, Gelb = Reconnect, Rot = Getrennt).
- **Aktiver Pfad (CWD):** Zeigt das aktuelle Arbeitsverzeichnis an. Ein Klick/Tap öffnet den interaktiven Verzeichnis-Browser zum schnellen Wechseln.
- **Modell-Badge & System-Info:** Schnelle Übersicht über das aktive Modell (`Gemini 3.7 Flash`), Uptime und IP-Adressen.
- **Top Actions:** Chat leeren (🗑️), Systeminfo (ℹ️) und Dark/Slate Theme-Umschaltung (🌙).

### 2. 💬 Hauptbereich (Chat & Visuals)
- **Mobile-First Responsive Layout:** Optimiert für iOS & Android (Safe Area Insets, Dynamic Viewport Height `100dvh`, Touch-Scrolling).
- **Echtzeit-KI-Streaming (SSE):** Live-Stream von Antigravity-Tokens und Tool-Ausführungen mit pulsierenden Status-Badges und sofortiger Eingabefeld-Reaktivierung.
- **Markdown-Rendering:**
  - Codeblöcke mit Syntax-Header, Sprache-Tag und 1-Klick **"Kopieren"**-Button.
  - GitHub Flavored Callouts (`> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`, `> [!CAUTION]`).
  - Markdown-Tabellen, Aufzählungslisten, Verlinkungen.
  - **Text-to-Speech (TTS):** Schaltfläche `🔊 Vorlesen` bei Assistenten-Antworten mit Ausblendung von Codeblöcken und Stopp-Option.
- **Bildvorschau & Vollbild-Lightbox:**
  - Thumbnails für hochgeladene und empfangene Bilder.
  - Antippen öffnet eine Lightbox mit Zoom, Download und Schließen.
- **Schnellbefehle-Leiste:** Schnellauswahl für `/help`, `/analyze`, `/goal`, `/plan`, `!ls`, `/status`, `!git status`, `/clear`.

### 3. 🔬 Visueller Code-Explorer & AST-Analyzer
- **Datei-Inspector Modal:** Tippe auf eine Datei im Verzeichnis-Browser, um den Inspector zu öffnen:
  - 📝 **Code & Editor:** Text- und Python-Dateien direkt im Smartphone-Browser ansehen, editieren und mit `💾 Speichern` sichern.
  - 🔬 **AST Funktions-Map:** Analysiert Python-Skripte lokal über `ast` in Module, Klassen, Methoden und Funktionen mit Argumenten & Docstrings. Jede Funktion hat einen `⚡ Erklären`-Button, der die Erklärung direkt im Chat anfordert.
  - 📊 **Ablaufdiagramm (Mermaid):** Visualisiert den Aufruf-Graph (wer ruft wen auf) automatisch als Flussdiagramm.
  - 🚀 **1-Klick Ausführung:** Mit `🚀 Ausführen` (`!python3 <datei>`) direkt im Dashboard testen.

### 4. ⌨️ Mobile Eingabeleiste & Spracheingabe
- **Multi-Line Textarea:** Passt sich beim Tippen automatisch der Höhe an (1 bis 6 Zeilen) und schrumpft nach dem Senden.
- **🎙️ Web Speech API Spracheingabe & Diktat:**
  - **Echtzeit-Transkription:** Live-Vorschau der gesprochenen Worte mit pulsierenden Audiowellen.
  - **Satzzeichen-Erkennung:** Automatische Konvertierung von gesprochenen Befehlen wie *"Punkt"*, *"Komma"*, *"Fragezeichen"*, *"Ausrufezeichen"*, *"Doppelpunkt"*, *"Neue Zeile"*.
  - **Störungsfreie Sprachaufnahme:** Zuverlässige Verkettung mehrerer Sprechsätze ohne Textduplizierung oder Abbrüche.
  - **Sprachauswahl:** Umschaltbar zwischen 🇩🇪 Deutsch (`de-DE`) und 🇺🇸 Englisch (`en-US`).
- **📸 Foto- & Kamera-Upload:**
  - Schnappschuss direkt über die Gerätekamera (`capture="environment"`).
  - Galerie-Upload für mehrere Bilder.
  - Client-seitige Auto-Komprimierung für ultraschnelle Übertragung auf Mobilgeräten.
  - Thumbnail-Vorschauleiste mit Einzel-Löschen (✕).
- **📋 Zwischenablage-Paste-Support (Clipboard):**
  - Screenshots oder Bilder direkt aus der Zwischenablage (`Strg+V` oder Long-Press Einfügen) werden automatisch erkannt, hochgeladen und an den Prompt angehängt.
- **Haptisches Feedback:** Taktile Vibration (`navigator.vibrate`) bei Klicks und Aktionen.

### 5. 📱 Termux:Widget & Homescreen 1-Tap Launcher
- **Hintergrund-Tasks:** Starten und Stoppen des Dashboards direkt über das Android **Termux:Widget** ohne störendes Terminalfenster.
- **Auto-Browser-Start:** Startet den Server im Hintergrund und öffnet sofort den Standard-Browser auf `http://localhost:8080`.
- **Einfache 1-Klick-Installation:** Fertig konfigurierte Skripte für `~/.shortcuts/tasks/`.

---

## 🚀 Schnellstart & Installation

### Option A: Termux:Widget (Empfohlen für Android)

1. Installiere das Addon **Termux:Widget** (z. B. via F-Droid).
2. Führe den Installer im Dashboard-Verzeichnis aus:
   ```bash
   cd ~/antigravity-dashboard
   ./shortcuts/install_widget.sh
   ```
3. Platziere das **Termux:Widget** auf deinem Android-Homescreen:
   - `antigravity-dashboard.sh` – Startet das Dashboard im Hintergrund und öffnet den Browser.
   - `antigravity-stop.sh` – Beendet das Dashboard sauber.

---

### Option B: Manuell über das Terminal

1. **Dashboard starten:**
   ```bash
   cd ~/antigravity-dashboard
   ./start.sh 8080
   ```
   *oder direkt via Python:*
   ```bash
   python3 ~/antigravity-dashboard/server.py 8080
   ```

2. **Im Browser öffnen:**
   - **Lokal auf dem Smartphone:** `http://localhost:8080`
   - **Im lokalen WLAN / Hotspot:** `http://[IP-ADRESSE]:8080` *(wird beim Start im Terminal angezeigt)*

---

## 📁 Termux Storage & Download-Integration

Um Dateien und Screenshots direkt mit dem Android-Dateisystem und Download-Ordner auszutauschen:
```bash
termux-setup-storage
```
Der Download-Ordner ist nun direkt unter `~/storage/downloads` erreichbar.

---

## 🛠️ Slash Commands & Shell Bridge

Im Dashboard können sowohl Antigravity-Befehle als auch direkte Shell-Kommandos eingegeben werden:
- `/analyze <datei.py>` – Analysiert ein Python-Skript grafisch (Klassen, Funktionen, Docstrings & Ablaufdiagramm)
- `!<befehl>` oder `/run <befehl>` – Führt einen Shell-Befehl in Termux im aktuellen Pfad aus (z. B. `!python3 main.py` oder `!git status`)
- `/cd <pfad>` – Wechselt das Arbeitsverzeichnis
- `/ls` – Listet Dateien im aktuellen Pfad auf
- `/status` – Zeigt Systemstatus und Dashboard-Verbindungsdaten
- `/plan <aufgabe>` – Erstellt einen Implementierungsplan
- `/goal <ziel>` – Startet ein autonomes Ziel
- `/clear` – Leert den Chatverlauf und startet frische KI-Session
- `/help` – Zeigt die Befehlsübersicht

---

## 📄 Lizenz

Dieses Projekt steht unter der [MIT License](LICENSE).
