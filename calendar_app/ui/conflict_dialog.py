"""
ConflictDialog — shown when a new appointment overlaps an existing one.

Lets the user choose:
  "Replace"  → overwrite the conflicting appointment
  "Keep Old" → cancel the add operation
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk

from models.appointment import Appointment

_INK      = "#111111"
_CANVAS   = "#FFFFFF"
_SOFT     = "#F8F9FA"
_HAIRLINE = "#E5E7EB"
_MUTED    = "#6B7280"
_BODY     = "#374151"
_ACCENT   = "#3B82F6"
_DANGER   = "#EF4444"
_WARN_BG  = "#FFF7ED"
_WARN_FG  = "#92400E"


class ConflictDialog:
    """
    Parameters
    ----------
    parent  : parent Tk window
    conflict: the existing Appointment that overlaps the new request

    After ``parent.wait_window(dialog.top)`` resolves, read:
      dialog.user_choice  →  "replace"  |  "cancel"
    """

    def __init__(self, parent: tk.Tk, conflict: Appointment) -> None:
        self.user_choice: str = "cancel"

        self.top = tk.Toplevel(parent)
        self.top.title("Time Conflict Detected")
        self.top.configure(bg=_CANVAS)
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.top.grab_set()

        parent.update_idletasks()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        w, h = 420, 300
        self.top.geometry(f"{w}x{h}+{px + (pw - w)//2}+{py + (ph - h)//2}")

        self._conflict = conflict
        self._build()

    def _build(self) -> None:
        root = self.top

        # ── Title ──────────────────────────────────────────────────
        title_bar = tk.Frame(root, bg=_CANVAS)
        title_bar.pack(fill="x", padx=24, pady=(20, 4))
        tk.Label(
            title_bar, text="⚠  Time Conflict Detected",
            bg=_CANVAS, fg=_INK, font=("Segoe UI", 12, "bold"),
        ).pack(side="left")

        ttk.Separator(root, orient="horizontal").pack(fill="x", padx=24, pady=(4, 16))

        # ── Warning card ───────────────────────────────────────────
        card = tk.Frame(root, bg=_WARN_BG, bd=0)
        card.pack(fill="x", padx=24, pady=(0, 16))
        inner = tk.Frame(card, bg=_WARN_BG)
        inner.pack(fill="x", padx=14, pady=12)

        tk.Label(
            inner, text="This time slot overlaps with:",
            bg=_WARN_BG, fg=_WARN_FG, font=("Segoe UI", 9),
        ).pack(anchor="w")

        appt = self._conflict
        tk.Label(
            inner, text=f'"{appt.name}"',
            bg=_WARN_BG, fg=_INK, font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(4, 0))

        time_str = (
            f"{appt.start_time.strftime('%Y-%m-%d  %H:%M')} – "
            f"{appt.end_time.strftime('%H:%M')}"
        )
        tk.Label(
            inner, text=time_str,
            bg=_WARN_BG, fg=_WARN_FG, font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(2, 0))

        if appt.location:
            tk.Label(
                inner, text=f"📍 {appt.location}",
                bg=_WARN_BG, fg=_MUTED, font=("Segoe UI", 9),
            ).pack(anchor="w", pady=(2, 0))

        # ── Question ───────────────────────────────────────────────
        tk.Label(
            root, text="Do you want to replace the existing appointment?",
            bg=_CANVAS, fg=_BODY, font=("Segoe UI", 10),
            wraplength=370, justify="left",
        ).pack(padx=24, anchor="w")

        # ── Buttons ────────────────────────────────────────────────
        ttk.Separator(root, orient="horizontal").pack(fill="x", padx=24, pady=(12, 0))
        btn_row = tk.Frame(root, bg=_CANVAS)
        btn_row.pack(fill="x", padx=24, pady=(12, 20))

        tk.Button(
            btn_row, text="Keep Old",
            bg=_SOFT, fg=_BODY, bd=0, cursor="hand2",
            font=("Segoe UI", 10), padx=16, pady=7,
            activebackground=_HAIRLINE, relief="flat",
            command=self._keep,
        ).pack(side="left")

        tk.Button(
            btn_row, text="Replace  →",
            bg=_DANGER, fg="white", bd=0, cursor="hand2",
            font=("Segoe UI", 10, "bold"), padx=16, pady=7,
            activebackground="#DC2626", activeforeground="white",
            relief="flat",
            command=self._replace,
        ).pack(side="right")

    def _keep(self) -> None:
        self.user_choice = "cancel"
        self.top.destroy()

    def _replace(self) -> None:
        self.user_choice = "replace"
        self.top.destroy()
