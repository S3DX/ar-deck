#!/usr/bin/env python3
import argparse
import csv
import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox, ttk

APP_NAME = "Account Picker"
EXPECTED_COUNT = 52
DEFAULT_ACCOUNTS_PATH = Path.home() / ".local" / "share" / "account-picker" / "accounts.tsv"


@dataclass(frozen=True)
class Account:
    index: int
    label: str
    username: str
    password: str

    @property
    def display_text(self) -> str:
        return f"{self.index:02d}. {self.label}  —  {self.username}"


def accounts_path() -> Path:
    env_path = os.environ.get("ACCOUNT_PICKER_ACCOUNTS", "").strip()
    return Path(env_path).expanduser() if env_path else DEFAULT_ACCOUNTS_PATH


def fail(message: str) -> None:
    raise ValueError(message)


def load_accounts(path: Path) -> list[Account]:
    if not path.exists():
        fail(f"Account data file not found: {path}")

    rows: list[Account] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        try:
            header = next(reader)
        except StopIteration:
            fail("Account data file is empty")

        if header != ["index", "label", "username", "password"]:
            fail("Invalid TSV header. Expected: index<TAB>label<TAB>username<TAB>password")

        for line_no, fields in enumerate(reader, start=2):
            if len(fields) != 4:
                fail(f"Malformed row {line_no}: expected exactly 4 tab-separated fields")
            index_text, label, username, password = fields
            try:
                index = int(index_text)
            except ValueError:
                fail(f"Malformed row {line_no}: index is not an integer")

            if not label:
                fail(f"Malformed row {line_no}: label is empty")
            if not username:
                fail(f"Malformed row {line_no}: username is empty")
            if not password:
                fail(f"Malformed row {line_no}: password is empty")
            if username != username.strip():
                fail(f"Malformed row {line_no}: username has leading/trailing whitespace")
            if password != password.strip():
                fail(f"Malformed row {line_no}: password has leading/trailing whitespace")

            rows.append(Account(index=index, label=label, username=username, password=password))

    if len(rows) != EXPECTED_COUNT:
        fail(f"Expected {EXPECTED_COUNT} accounts, found {len(rows)}")

    expected_indexes = list(range(1, EXPECTED_COUNT + 1))
    actual_indexes = [account.index for account in rows]
    if actual_indexes != expected_indexes:
        fail("Account indexes must be sequential from 1 to 52")

    usernames = [account.username for account in rows]
    if len(set(usernames)) != len(usernames):
        fail("Duplicate usernames detected")

    return rows


def detect_backend() -> str | None:
    session = os.environ.get("XDG_SESSION_TYPE", "").lower()
    if session == "wayland" and shutil.which("wtype"):
        return "wtype"
    if shutil.which("xdotool"):
        return "xdotool"
    if shutil.which("wtype"):
        return "wtype"
    return None


def run_checked(args: list[str]) -> None:
    subprocess.run(args, check=True)


def type_text(backend: str, text: str) -> None:
    if backend == "xdotool":
        run_checked(["xdotool", "type", "--clearmodifiers", "--delay", "20", text])
    elif backend == "wtype":
        run_checked(["wtype", text])
    else:
        raise RuntimeError("No supported typing backend is available")


def press_tab_once(backend: str) -> None:
    if backend == "xdotool":
        run_checked(["xdotool", "key", "--clearmodifiers", "Tab"])
    elif backend == "wtype":
        run_checked(["wtype", "-k", "Tab"])
    else:
        raise RuntimeError("No supported typing backend is available")


def fill_account(account: Account) -> None:
    backend = detect_backend()
    if backend is None:
        raise RuntimeError("No fake-typing backend found. Install xdotool for X11 or wtype for Wayland.")
    type_text(backend, account.username)
    press_tab_once(backend)
    type_text(backend, account.password)


class AccountPickerApp:
    def __init__(self, root: tk.Tk, accounts: list[Account]) -> None:
        self.root = root
        self.accounts = accounts
        self.filtered_accounts = list(accounts)
        self.selected_account: Account | None = None
        self.countdown_job: str | None = None
        self.countdown_left = 0
        self.is_counting_down = False

        self.root.title(APP_NAME)
        self.root.geometry("620x680")
        self.root.minsize(620, 680)
        self.root.maxsize(620, 680)
        self.root.resizable(False, False)
        self.root.configure(bg="#181a20")
        self.center_window()

        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Select an account, press Fill, then focus the username field.")
        self.selected_var = tk.StringVar(value="No account selected")

        self.build_ui()
        self.refresh_list()

    def center_window(self) -> None:
        self.root.update_idletasks()
        width = 620
        height = 680
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = max((screen_width - width) // 2, 0)
        y = max((screen_height - height) // 2, 0)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def build_ui(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#181a20")
        style.configure("TLabel", background="#181a20", foreground="#eef2ff", font=("Sans", 11))
        style.configure("Title.TLabel", font=("Sans", 20, "bold"), foreground="#ffffff")
        style.configure("Muted.TLabel", foreground="#9aa4b2")
        style.configure("TButton", padding=10, font=("Sans", 11, "bold"))
        style.configure("Accent.TButton", padding=10, font=("Sans", 12, "bold"))

        main = ttk.Frame(self.root, padding=18)
        main.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(main, text=APP_NAME, style="Title.TLabel")
        title.pack(anchor="w")

        subtitle = ttk.Label(
            main,
            text="Steam Deck Desktop Mode account selector. Passwords are hidden from the list.",
            style="Muted.TLabel",
        )
        subtitle.pack(anchor="w", pady=(4, 14))

        search_label = ttk.Label(main, text="Search")
        search_label.pack(anchor="w")
        search = tk.Entry(
            main,
            textvariable=self.search_var,
            bg="#242833",
            fg="#ffffff",
            insertbackground="#ffffff",
            relief=tk.FLAT,
            font=("Sans", 13),
        )
        search.pack(fill=tk.X, ipady=8, pady=(4, 12))
        search.bind("<KeyRelease>", lambda _event: self.apply_filter())

        list_frame = ttk.Frame(main)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(
            list_frame,
            bg="#101219",
            fg="#eef2ff",
            selectbackground="#2563eb",
            selectforeground="#ffffff",
            highlightthickness=1,
            highlightbackground="#2f3542",
            activestyle="none",
            relief=tk.FLAT,
            font=("Sans", 11),
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox.bind("<<ListboxSelect>>", lambda _event: self.on_select())
        self.listbox.bind("<Return>", lambda event: "break")
        self.listbox.bind("<KP_Enter>", lambda event: "break")

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.configure(yscrollcommand=scrollbar.set)

        selected = ttk.Label(main, textvariable=self.selected_var)
        selected.pack(anchor="w", pady=(12, 4))

        status = ttk.Label(main, textvariable=self.status_var, style="Muted.TLabel", wraplength=570)
        status.pack(anchor="w", pady=(0, 12))

        buttons = ttk.Frame(main)
        buttons.pack(fill=tk.X)

        self.fill_button = ttk.Button(buttons, text="Fill Selected Account", style="Accent.TButton", command=self.start_countdown)
        self.fill_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        self.cancel_button = ttk.Button(buttons, text="Cancel", command=self.cancel_countdown)
        self.cancel_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))

    def apply_filter(self) -> None:
        query = self.search_var.get().strip().lower()
        if not query:
            self.filtered_accounts = list(self.accounts)
        else:
            self.filtered_accounts = [
                account for account in self.accounts
                if query in account.label.lower() or query in account.username.lower()
            ]
        self.refresh_list()

    def refresh_list(self) -> None:
        self.listbox.delete(0, tk.END)
        for account in self.filtered_accounts:
            self.listbox.insert(tk.END, account.display_text)

    def on_select(self) -> None:
        selection = self.listbox.curselection()
        if not selection:
            self.selected_account = None
            self.selected_var.set("No account selected")
            return
        self.selected_account = self.filtered_accounts[selection[0]]
        self.selected_var.set(f"Selected: {self.selected_account.label} — {self.selected_account.username}")

    def start_countdown(self) -> None:
        if self.is_counting_down:
            return
        if self.selected_account is None:
            messagebox.showwarning(APP_NAME, "Select an account first.")
            return
        self.countdown_left = 5
        self.is_counting_down = True
        self.fill_button.state(["disabled"])
        self.status_var.set("Countdown started. Focus the target username field now.")
        self.tick()

    def tick(self) -> None:
        if not self.is_counting_down:
            return
        if self.countdown_left <= 0:
            self.status_var.set("Typing now...")
            self.countdown_job = None
            account = self.selected_account
            self.is_counting_down = False
            self.fill_button.state(["!disabled"])
            if account is not None:
                threading.Thread(target=self.type_selected, args=(account,), daemon=True).start()
            return
        self.status_var.set(f"Typing in {self.countdown_left} seconds. Focus the target username field.")
        self.countdown_left -= 1
        self.countdown_job = self.root.after(1000, self.tick)

    def cancel_countdown(self) -> None:
        if self.countdown_job is not None:
            self.root.after_cancel(self.countdown_job)
            self.countdown_job = None
        self.is_counting_down = False
        self.countdown_left = 0
        self.fill_button.state(["!disabled"])
        self.status_var.set("Cancelled. Nothing was typed.")

    def type_selected(self, account: Account) -> None:
        try:
            fill_account(account)
        except Exception as exc:
            self.root.after(0, lambda: self.show_error(str(exc)))
        else:
            self.root.after(0, lambda: self.status_var.set("Done. Username, one Tab, and password were typed."))

    def show_error(self, message: str) -> None:
        self.status_var.set("Typing failed.")
        messagebox.showerror(APP_NAME, message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Steam Deck Account Picker")
    parser.add_argument("--validate", action="store_true", help="Validate account data without launching the UI")
    args = parser.parse_args()

    try:
        loaded_accounts = load_accounts(accounts_path())
    except Exception as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        return 1

    if args.validate:
        print(f"Validation passed: {len(loaded_accounts)} accounts")
        return 0

    root = tk.Tk()
    AccountPickerApp(root, loaded_accounts)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
