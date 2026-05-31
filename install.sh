#!/usr/bin/env bash
set -euo pipefail

APP_NAME="Deck Virtual Paste"
SCRIPT_NAME="deck-virtual-paste"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_SCRIPT="$SRC_DIR/$SCRIPT_NAME"
BIN_DIR="$HOME/.local/bin"
BIN_PATH="$BIN_DIR/$SCRIPT_NAME"
DESKTOP_DIR="$HOME/Desktop"
DESKTOP_FILE="$DESKTOP_DIR/$APP_NAME.desktop"

if [[ ! -f "$SRC_SCRIPT" ]]; then
  echo "Error: $SCRIPT_NAME not found next to install.sh"
  exit 1
fi

mkdir -p "$BIN_DIR" "$DESKTOP_DIR"
cp "$SRC_SCRIPT" "$BIN_PATH"
chmod +x "$BIN_PATH"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Deck Virtual Paste
Comment=Type clipboard text as fake keyboard input
Exec=$BIN_PATH
Icon=input-keyboard
Terminal=false
Categories=Utility;
EOF

chmod +x "$DESKTOP_FILE"
gio set "$DESKTOP_FILE" metadata::trusted true >/dev/null 2>&1 || true

if ! command -v xdotool >/dev/null 2>&1 && ! command -v wtype >/dev/null 2>&1; then
  echo "Warning: no fake-typing backend found. Install xdotool for X11 or wtype for Wayland if typing fails."
fi

if ! command -v kdialog >/dev/null 2>&1; then
  echo "Warning: kdialog not found. The app will use terminal fallback UI."
fi

echo "Installed. Look on Desktop for: Deck Virtual Paste"
