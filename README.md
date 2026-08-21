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
- **Markdown-Rendering:**
  - Codeblöcke mit Syntax-Header, Sprache-Tag und 1-Klick **"Kopieren"**-Button.
  - GitHub Flavored Callouts (`> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`, `> [!CAUTION]`).
  - Markdown-Tabellen, Aufzählungslisten, Verlinkungen.
  - **Text-to-Speech (TTS):** Schaltfläche `🔊 Vorlesen` bei Assistenten-Antworten.
- **Bildvorschau & Vollbild-Lightbox:**
  - Thumbnails für hochgeladene und empfangene Bilder.
  - Antippen öffnet eine Lightbox mit Zoom, Download und Schließen.
- **Schnellbefehle-Leiste:** Schnellauswahl für `/help`, `/goal`, `/plan`, `!ls`, `/status`, `!git status`, `/clear`.

### 3. ⌨️ Mobile Eingabeleiste unten
- **Multi-Line Textarea:** Passt sich beim Tippen automatisch der Höhe an (1 bis 6 Zeilen) und schrumpft nach dem Senden.
- **🎙️ Push-to-Talk Mikrofon-Button (Web Speech API):**
  - **Push-to-Talk:** Gedrückt halten zum Sprechen, Loslassen fügt den Text ein.
  - **Tap-Modus:** Tippen öffnet das Sprach-Overlay mit pulsierenden Audiowellen und Echtzeit-Erkennung.
  - Sprachauswahl für 🇩🇪 Deutsch (`de-DE`) und 🇺🇸 Englisch (`en-US`).
- **📸 Foto- & Kamera-Upload:**
  - Schnappschuss direkt über die Gerätekamera (`capture="environment"`).
  - Galerie-Upload für mehrere Bilder.
  - Client-seitige Auto-Komprimierung für ultraschnelle Übertragung auf Mobilgeräten.
  - Thumbnail-Vorschauleiste mit Einzel-Löschen (✕).
- **📋 Zwischenablage-Paste-Support (Clipboard):**
  - Screenshots oder Bilder direkt aus der Zwischenablage (`Strg+V` oder Long-Press Einfügen) werden automatisch erkannt, hochgeladen und an den Prompt angehängt.
- **Haptisches Feedback:** Taktile Vibration (`navigator.vibrate`) bei Klicks und Aktionen.

---

## 🚀 Schnellstart

### Dashboard starten:
```bash
cd ~/antigravity-dashboard
./start.sh 8080
```
*oder direkt via Python:*
```bash
python3 ~/antigravity-dashboard/server.py 8080
```

### Auf dem Smartphone / Browser öffnen:
- **Lokal auf dem Gerät:** `http://localhost:8080`
- **Im gleichen WLAN / Hotspot:** `http://[IP-ADRESSE]:8080` *(die genaue WLAN-IP wird beim Start im Terminal angezeigt)*

---

## 🛠️ Slash Commands & Shell Bridge

Im Dashboard können sowohl Antigravity-Befehle als auch direkte Shell-Kommandos eingegeben werden:
- `!<befehl>` oder `/run <befehl>` – Führt einen Shell-Befehl in Termux im aktuellen Pfad aus (z. B. `!python3 main.py` oder `!git status`)
- `/cd <pfad>` – Wechselt das Arbeitsverzeichnis
- `/ls` – Listet Dateien im aktuellen Pfad auf
- `/status` – Zeigt Systemstatus und Dashboard-Verbindungsdaten
- `/plan <aufgabe>` – Erstellt einen Implementierungsplan
- `/goal <ziel>` – Startet ein autonomes Ziel
- `/clear` – Leert den Chatverlauf
- `/help` – Zeigt die Befehlsübersicht
