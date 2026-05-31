# Deck Virtual Paste

Tiny local-only Steam Deck Desktop Mode utility that types clipboard text as fake keyboard input instead of using normal paste.

## Install on Steam Deck

```bash
git clone --depth=1 https://github.com/S3DX/ar-deck.git
cd ar-deck
chmod +x install.sh
./install.sh
```

## Usage

1. Copy password/text.
2. Open Steam login.
3. Launch `Deck Virtual Paste` from Desktop.
4. Tap `TYPE CLIPBOARD IN 5 SECONDS`.
5. Tap the Steam password box.
6. Wait for auto-typing.
7. Press login manually.

## Notes

- It never uses Ctrl+V.
- It never uses normal clipboard paste.
- It does not display, store, or log clipboard content.
- It types character-by-character using `xdotool` on X11 or `wtype` on Wayland when available.
