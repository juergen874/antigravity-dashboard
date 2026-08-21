#!/usr/bin/env bash
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

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Fehler: python3 wurde nicht gefunden. Bitte installiere Python ('pkg install python')."
    exit 1
fi

echo "🚀 Starte Webserver..."
cd "$DIR"
exec python3 server.py "$PORT"
