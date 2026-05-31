#!/usr/bin/env bash
set -euo pipefail

APP_NAME="Account Picker"
SCRIPT_NAME="account-picker.py"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_APP="$SRC_DIR/$SCRIPT_NAME"
SRC_ACCOUNTS="$SRC_DIR/accounts.tsv"

APP_DIR="$HOME/.local/share/account-picker"
BIN_DIR="$HOME/.local/bin"
BIN_PATH="$BIN_DIR/account-picker"
DESKTOP_DIR="$HOME/Desktop"
DESKTOP_FILE="$DESKTOP_DIR/Account Picker.desktop"
ACCOUNTS_PATH="$APP_DIR/accounts.tsv"

if [[ "${1:-}" == "--dry-run" ]]; then
  echo "Dry run: installer syntax OK"
  exit 0
fi

if [[ ! -f "$SRC_APP" ]]; then
  echo "Error: $SCRIPT_NAME not found next to install.sh"
  exit 1
fi

if [[ ! -f "$SRC_ACCOUNTS" ]]; then
  echo "Error: accounts.tsv not found next to install.sh"
  echo "Create accounts.tsv locally before running this installer."
  exit 1
fi

mkdir -p "$APP_DIR" "$BIN_DIR" "$DESKTOP_DIR"

install -m 0755 "$SRC_APP" "$APP_DIR/account-picker.py"
install -m 0600 "$SRC_ACCOUNTS" "$ACCOUNTS_PATH"

cat > "$BIN_PATH" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
export ACCOUNT_PICKER_ACCOUNTS="$HOME/.local/share/account-picker/accounts.tsv"
exec python3 "$HOME/.local/share/account-picker/account-picker.py" "$@"
EOF
chmod +x "$BIN_PATH"

if ! "$BIN_PATH" --validate >/dev/null; then
  echo "Error: installed Account Picker validation failed"
  exit 1
fi

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Account Picker
Comment=Select a stored account and type username, one Tab, then password
Exec=$BIN_PATH
Icon=input-keyboard
Terminal=false
Categories=Utility;
EOF

chmod +x "$DESKTOP_FILE"
gio set "$DESKTOP_FILE" metadata::trusted true >/dev/null 2>&1 || true

rm -f "$HOME/Desktop/Deck Virtual Paste.desktop" \
      "$HOME/.local/bin/deck-virtual-paste"

if ! command -v xdotool >/dev/null 2>&1 && ! command -v wtype >/dev/null 2>&1; then
  echo "Warning: no fake-typing backend found. Install xdotool for X11 or wtype for Wayland if typing fails."
fi

echo "Installed. Look on Desktop for: Account Picker"
