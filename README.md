# Account Picker

Steam Deck Desktop Mode / KDE utility for selecting a stored account and typing:

```text
username → one Tab → password → stop
```

The app does **not** press Enter.

## Files

- `account-picker.py` — Tkinter UI and typing automation.
- `install.sh` — local Steam Deck installer.
- `accounts.example.tsv` — safe example format only. It does not contain real credentials.

Real credentials must be created locally on the Steam Deck as `accounts.tsv` before running the installer. Do not commit real `accounts.tsv` to GitHub.

## Account file format

`accounts.tsv` must use this exact header:

```text
index	label	username	password
```

The app validates exactly 52 account rows, sequential indexes from 1 to 52, exactly four tab-separated fields, and no leading/trailing whitespace around usernames or passwords.

## Install

Use the one-shot install command generated outside the repository. It should:

1. Clone this repo.
2. Write `accounts.tsv` locally on the Steam Deck.
3. Run `install.sh`.

The installer places files at:

```text
~/.local/share/account-picker
~/.local/bin/account-picker
~/Desktop/Account Picker.desktop
```

## UI behavior

- Fixed-size floating dark KDE-friendly window.
- Search/filter box.
- Scrollable account list.
- Rows show label + username only.
- Passwords are never displayed in the list.
- 5-second countdown before typing.
- Cancel stops countdown before typing begins.

## Automation behavior

When Fill is triggered:

1. Type username.
2. Press Tab exactly once.
3. Type password.
4. Stop.

Backends:

- `xdotool` on X11
- `wtype` on Wayland

If neither backend exists, the app reports the missing backend.
