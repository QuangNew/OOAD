from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from models.user import User
from storage.file_storage import FileStorage


_INK = "#111111"
_CANVAS = "#FFFFFF"
_SOFT = "#F8F9FA"
_CARD = "#F5F5F5"
_HAIRLINE = "#E5E7EB"
_MUTED = "#6B7280"
_BODY = "#374151"
_ACCENT = "#3B82F6"


class AuthUI:
    def __init__(self) -> None:
        self.authenticated_user: User | None = None
        self.root = tk.Tk()
        self.root.title("Calendar App Login")
        self.root.geometry("560x500")
        self.root.minsize(500, 460)
        self.root.configure(bg=_CANVAS)

        self._setup_styles()
        self._build_layout()

    def _setup_styles(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", background=_CANVAS, foreground=_INK, font=("Segoe UI", 10))
        style.configure("TFrame", background=_CANVAS)
        style.configure("TLabel", background=_CANVAS, foreground=_INK)
        style.configure("TNotebook", background=_CANVAS, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(14, 8), font=("Segoe UI", 10, "bold"))
        style.configure("TEntry", fieldbackground=_CANVAS, bordercolor=_HAIRLINE, relief="flat")
        style.map("TEntry", bordercolor=[("focus", _ACCENT), ("!focus", _HAIRLINE)])

    def _build_layout(self) -> None:
        shell = tk.Frame(self.root, bg=_CANVAS)
        shell.pack(fill="both", expand=True, padx=28, pady=24)

        hero = tk.Frame(shell, bg=_CANVAS)
        hero.pack(fill="x", pady=(0, 16))
        tk.Label(
            hero,
            text="Calendar Appointment Manager",
            bg=_CANVAS,
            fg=_INK,
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w")
        tk.Label(
            hero,
            text="Đăng nhập hoặc tạo tài khoản mới để dùng lịch cá nhân của riêng bạn.",
            bg=_CANVAS,
            fg=_MUTED,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(6, 0))

        card = tk.Frame(shell, bg=_CARD, highlightbackground=_HAIRLINE, highlightthickness=1)
        card.pack(fill="both", expand=True)

        body = tk.Frame(card, bg=_CARD)
        body.pack(fill="both", expand=True, padx=18, pady=18)

        notebook = ttk.Notebook(body)
        notebook.pack(fill="both", expand=True)

        login_tab = tk.Frame(notebook, bg=_CARD)
        register_tab = tk.Frame(notebook, bg=_CARD)
        notebook.add(login_tab, text="Login")
        notebook.add(register_tab, text="Register")

        self._build_login_tab(login_tab)
        self._build_register_tab(register_tab)

        hint_text = "Tài khoản mới sẽ được tạo sẵn 3 group meeting demo để bạn test nhanh."
        if not FileStorage.load_accounts():
            notebook.select(register_tab)
            hint_text = "Chưa có tài khoản nào. Hãy tạo tài khoản đầu tiên để bắt đầu."

        tk.Label(
            body,
            text=hint_text,
            bg=_CARD,
            fg=_MUTED,
            font=("Segoe UI", 9),
            wraplength=440,
            justify="left",
        ).pack(fill="x", pady=(12, 0))

    def _build_login_tab(self, parent: tk.Frame) -> None:
        self._login_username = tk.StringVar()
        self._login_password = tk.StringVar()

        form = tk.Frame(parent, bg=_CARD)
        form.pack(fill="both", expand=True, padx=10, pady=14)
        form.grid_columnconfigure(0, weight=1)

        tk.Label(
            form,
            text="Đăng nhập",
            bg=_CARD,
            fg=_INK,
            font=("Segoe UI", 13, "bold"),
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            form,
            text="Dùng username và password của bạn.",
            bg=_CARD,
            fg=_MUTED,
            font=("Segoe UI", 10),
        ).grid(row=1, column=0, sticky="w", pady=(4, 16))

        self._add_entry(form, 2, "Username", self._login_username)
        self._add_entry(form, 4, "Password", self._login_password, show="*")

        tk.Button(
            form,
            text="Login",
            bg=_ACCENT,
            fg="white",
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=16,
            pady=8,
            relief="flat",
            activebackground="#2563EB",
            command=self._handle_login,
        ).grid(row=6, column=0, sticky="ew", pady=(12, 0))

    def _build_register_tab(self, parent: tk.Frame) -> None:
        self._register_full_name = tk.StringVar()
        self._register_username = tk.StringVar()
        self._register_password = tk.StringVar()
        self._register_confirm = tk.StringVar()

        form = tk.Frame(parent, bg=_CARD)
        form.pack(fill="both", expand=True, padx=10, pady=14)
        form.grid_columnconfigure(0, weight=1)

        tk.Label(
            form,
            text="Tạo tài khoản",
            bg=_CARD,
            fg=_INK,
            font=("Segoe UI", 13, "bold"),
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            form,
            text="Bạn sẽ đăng nhập ngay sau khi đăng ký thành công.",
            bg=_CARD,
            fg=_MUTED,
            font=("Segoe UI", 10),
        ).grid(row=1, column=0, sticky="w", pady=(4, 16))

        self._add_entry(form, 2, "Full Name", self._register_full_name)
        self._add_entry(form, 4, "Username", self._register_username)
        self._add_entry(form, 6, "Password", self._register_password, show="*")
        self._add_entry(form, 8, "Confirm Password", self._register_confirm, show="*")

        tk.Button(
            form,
            text="Create Account",
            bg=_ACCENT,
            fg="white",
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=16,
            pady=8,
            relief="flat",
            activebackground="#2563EB",
            command=self._handle_register,
        ).grid(row=10, column=0, sticky="ew", pady=(12, 0))

    def _add_entry(
        self,
        parent: tk.Frame,
        row: int,
        label_text: str,
        variable: tk.StringVar,
        *,
        show: str | None = None,
    ) -> None:
        tk.Label(
            parent,
            text=label_text,
            bg=_CARD,
            fg=_BODY,
            font=("Segoe UI", 9, "bold"),
        ).grid(row=row, column=0, sticky="w", pady=(0, 4))
        entry = ttk.Entry(parent, textvariable=variable, font=("Segoe UI", 10), show=show or "")
        entry.grid(row=row + 1, column=0, sticky="ew", ipady=5, pady=(0, 12))

    def _handle_login(self) -> None:
        user = FileStorage.authenticate_user(
            self._login_username.get(),
            self._login_password.get(),
        )
        if user is None:
            messagebox.showerror(
                "Login Failed",
                "Username hoặc password không đúng.",
                parent=self.root,
            )
            return
        self.authenticated_user = user
        self.root.destroy()

    def _handle_register(self) -> None:
        if self._register_password.get() != self._register_confirm.get():
            messagebox.showerror(
                "Register Failed",
                "Password xác nhận chưa khớp.",
                parent=self.root,
            )
            return

        try:
            user = FileStorage.register_user(
                self._register_full_name.get(),
                self._register_username.get(),
                self._register_password.get(),
            )
        except ValueError as exc:
            messagebox.showerror("Register Failed", str(exc), parent=self.root)
            return

        FileStorage.seed_demo_meetings_for_user(user)
        messagebox.showinfo(
            "Account Created",
            "Tài khoản đã được tạo và đã thêm sẵn 3 group meeting demo cho bạn.",
            parent=self.root,
        )
        self.authenticated_user = user
        self.root.destroy()

    def run(self) -> User | None:
        self.root.mainloop()
        return self.authenticated_user