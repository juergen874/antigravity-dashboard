#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
# Termux Shortcut: Stop Antigravity Dashboard
# ==============================================================================

PORT=8080

if pgrep -f "server.py $PORT" > /dev/null 2>&1; then
    pkill -f "server.py $PORT"
    echo "Dashboard (Port $PORT) beendet."
else
    echo "Dashboard lief nicht."
fi
