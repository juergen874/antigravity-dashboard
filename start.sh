#!/data/data/com.termux/files/usr/bin/env bash
# ==============================================================================
# Antigravity CLI Mobile Web Dashboard Starter
# ==============================================================================

set -e
PORT=${1:-8080}
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================================="
echo "⚡ Antigravity CLI Mobile Web Dashboard"
echo "=========================================================="
echo "📁 Dashboard-Verzeichnis: $DIR"
echo "🌐 Port: $PORT"

if [ -f "$HOME/.gemini_api_key" ]; then
    export GEMINI_API_KEY="$(cat "$HOME/.gemini_api_key" | tr -d '\r\n')"
    export GOOGLE_API_KEY="$GEMINI_API_KEY"
    echo "🔑 Gemini API-Key geladen."
fi

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Fehler: python3 wurde nicht gefunden. Bitte installiere Python ('pkg install python')."
    exit 1
fi

# Browser im Hintergrund öffnen sobald der Server bereit ist
echo "🌐 Öffne Dashboard im Browser..."
(
    sleep 1
    URL="http://localhost:$PORT"
    if command -v termux-open-url &> /dev/null; then
        termux-open-url "$URL"
    elif command -v termux-open &> /dev/null; then
        termux-open "$URL"
    elif command -v xdg-open &> /dev/null; then
        xdg-open "$URL"
    fi
) &

echo "🚀 Starte Webserver..."
cd "$DIR"
exec python3 server.py "$PORT"
