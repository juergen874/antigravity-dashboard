<p align="center">
  <b><a href="#-english">🇬🇧 English</a></b> &nbsp;•&nbsp; <b><a href="#-deutsch">🇩🇪 Deutsch</a></b>
</p>

---

<a name="-english"></a>
# ⚡ Antigravity CLI • Mobile Web Dashboard

An ultra-lightweight, modern, and mobile-friendly web dashboard for the **Google Antigravity CLI** and Termux/Linux development environments.

---

## ✨ Features Overview

### 1. 🟢 Top Status Header
- **Real-Time Connection Indicator:** Live pulse badge (Green = Connected with ping latency in ms, Yellow = Reconnecting, Red = Disconnected).
- **Active Path (CWD):** Displays current working directory. Click/tap to open an interactive directory browser for quick navigation.
- **Model Badge & Diagnostics:** Quick overview of the active LLM (`Gemini Flash`), uptime, and local network IPs.
- **Top Actions:** Clear chat (🗑️), System diagnostics (ℹ️), and Dark/Slate Theme switcher (🌙).

### 2. 💬 Main Area (Chat & Visuals)
- **Mobile-First Responsive Layout:** Tailored for Android & iOS (Safe Area Insets, Dynamic Viewport Height `100dvh`, smooth touch scrolling).
- **Real-Time Streaming (SSE):** Live streaming of Antigravity tokens and tool executions with animated progress badges.
- **Rich Markdown Rendering:**
  - Syntax-highlighted code blocks with language header and 1-click **Copy** button.
  - GitHub Flavored Callouts (`> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`, `> [!CAUTION]`).
  - Tables, bullet lists, interactive links.
  - **Text-to-Speech (TTS):** Integrated `🔊 Read aloud` option for assistant messages with automatic code-block skipping and pause controls.
- **Image Preview & Fullscreen Lightbox:**
  - Thumbnails for uploaded and generated images.
  - Tap opens a responsive lightbox with zoom, download, and close options.
- **Quick-Actions Bar:** Fast chips for `/help`, `/analyze`, `/goal`, `/plan`, `!ls`, `/status`, `!git status`, `/clear`.

### 3. 🔬 Visual Code Explorer & AST Analyzer
- **File Inspector Modal:** Tap any file in the directory browser to open:
  - 📝 **Code Viewer & Editor:** View and edit text/Python files directly in your mobile browser with `💾 Save`.
  - 🔬 **AST Function Map:** Parses Python scripts locally via `ast` into modules, classes, methods, and functions with arguments and docstrings. Each function includes a `⚡ Explain` shortcut that requests instant analysis in chat.
  - 📊 **Flowchart (Mermaid):** Visualizes call relationships automatically as a responsive diagram.
  - 🚀 **1-Click Test Execution:** Run scripts directly inside Termux with `🚀 Run` (`!python3 <file>`).

### 4. ⌨️ Mobile Input Bar & Dictation
- **Auto-Expanding Textarea:** Dynamically scales from 1 to 6 lines and collapses automatically upon submission.
- **🎙️ Web Speech API Voice Input & Dictation:**
  - **Live Transcription:** Real-time speech preview with pulsing waveform animation.
  - **Punctuation Command Parsing:** Automatically converts spoken words like *"Period"*, *"Comma"*, *"Question mark"*, *"Exclamation point"*, *"Colon"*, *"New line"*.
  - **Continuous Dictation:** Seamless sentence chaining without duplicates or interruptions.
  - **Language Selector:** Toggle between 🇩🇪 German (`de-DE`) and 🇺🇸 English (`en-US`).
- **📸 Camera & Photo Attachments:**
  - Direct camera snapshots (`capture="environment"`).
  - Multi-image gallery picker.
  - Automatic client-side image compression for mobile transfers.
  - Interactive preview chips with individual delete (✕).
- **📋 Clipboard Paste Support:**
  - Screenshots or copied image bitmaps (`Ctrl+V` or long-press paste) are automatically intercepted, uploaded, and attached to the prompt.
- **Haptic Feedback:** Tactile vibration (`navigator.vibrate`) on key actions.

### 5. 📱 Termux:Widget & 1-Tap Homescreen Launcher
- **Background Tasks:** Launch and stop the dashboard directly from your Android **Termux:Widget** without terminal clutter.
- **Auto-Browser Launch:** Automatically boots the server and opens `http://localhost:8080` in your default browser.
- **Preconfigured Scripts:** Ready-to-use shortcuts for `~/.shortcuts/tasks/`.

---

## 🚀 Quick Start & Installation

### Option A: Termux:Widget (Recommended for Android)

1. Install **Termux:Widget** (via F-Droid).
2. Run the installer inside the dashboard folder:
   ```bash
   cd ~/antigravity-dashboard
   ./shortcuts/install_widget.sh
   ```
3. Place the **Termux:Widget** on your Android homescreen:
   - `antigravity-dashboard.sh` – Starts server in background and opens browser.
   - `antigravity-stop.sh` – Shuts down server cleanly.

---

### Option B: Terminal Command Line

1. **Launch Dashboard:**
   ```bash
   cd ~/antigravity-dashboard
   ./start.sh 8080
   ```
   *or directly via Python:*
   ```bash
   python3 ~/antigravity-dashboard/server.py 8080
   ```

2. **Open in Browser:**
   - **On Device:** `http://localhost:8080`
   - **Local Wi-Fi / Hotspot:** `http://[IP-ADDRESS]:8080` *(displayed on startup)*

---

## 🛠️ Slash Commands & Shell Bridge

- `/analyze <file.py>` – Graphically inspects a Python file (AST, functions, Mermaid flow)
- `!<command>` or `/run <command>` – Executes a shell command in Termux (e.g., `!python3 main.py` or `!git status`)
- `/cd <path>` – Changes working directory
- `/ls` – Lists files in active directory
- `/status` – Displays server status and network info
- `/plan <task>` – Formulates an implementation plan
- `/goal <goal>` – Executes an autonomous multi-step goal
- `/clear` – Clears chat history and restarts session
- `/help` – Displays command help

---

## 📄 License

Licensed under the [MIT License](LICENSE).

---
---

<a name="-deutsch"></a>
# 🇩🇪 Deutsche Beschreibung

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
- **Echtzeit-KI-Streaming (SSE):** Live-Stream von Antigravity-Tokens und Tool-Ausführungen mit pulsierenden Status-Badges.
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
