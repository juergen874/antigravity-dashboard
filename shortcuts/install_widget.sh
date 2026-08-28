#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
# Antigravity Dashboard - Termux:Widget Shortcuts Installer
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHORTCUTS_TASKS_DIR="$HOME/.shortcuts/tasks"

echo "📱 Installiere Termux:Widget Shortcuts..."

mkdir -p "$SHORTCUTS_TASKS_DIR"

cp "$SCRIPT_DIR/tasks/antigravity-dashboard.sh" "$SHORTCUTS_TASKS_DIR/"
cp "$SCRIPT_DIR/tasks/antigravity-stop.sh" "$SHORTCUTS_TASKS_DIR/"

chmod +x "$SHORTCUTS_TASKS_DIR/antigravity-dashboard.sh"
chmod +x "$SHORTCUTS_TASKS_DIR/antigravity-stop.sh"

echo "✅ Erfolgreich installiert in $SHORTCUTS_TASKS_DIR:"
echo "   - antigravity-dashboard.sh (Starten & Browser öffnen im Hintergrund)"
echo "   - antigravity-stop.sh (Dashboard beenden)"
echo ""
echo "💡 Tipp: Füge das 'Termux:Widget' auf deinem Android-Homescreen hinzu,"
echo "   um das Dashboard mit einem Fingertipp lautlos im Hintergrund zu starten!"
