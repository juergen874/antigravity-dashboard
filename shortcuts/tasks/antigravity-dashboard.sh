#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
# Termux Shortcut: Start Antigravity Dashboard & Open in Browser
# ==============================================================================

PORT=8080
DASHBOARD_DIR="$HOME/antigravity-dashboard"
URL="http://localhost:$PORT"

# Check if dashboard server is already running
if ! pgrep -f "server.py $PORT" > /dev/null 2>&1; then
    cd "$DASHBOARD_DIR" || exit 1
    nohup python3 server.py "$PORT" > /dev/null 2>&1 &
    sleep 1
fi

# Open Dashboard in the default Android browser
termux-open-url "$URL"
