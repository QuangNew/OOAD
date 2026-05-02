"""
GroupMeetingDialog — shown when a new appointment matches an existing
GroupMeeting by name + duration.

Lets the user choose:
  "Join"      → add current user to the group meeting's participants
  "New Appt"  → create a separate personal appointment (no group join)
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk

from models.group_meeting import GroupMeeting

_INK      = "#111111"
_CANVAS   = "#FFFFFF"
_SOFT     = "#F8F9FA"
_HAIRLINE = "#E5E7EB"
_MUTED    = "#6B7280"
_BODY     = "#374151"
_ACCENT   = "#3B82F6"
_INFO_BG  = "#EFF6FF"
_INFO_FG  = "#1E40AF"


class GroupMeetingDialog:
    """
    Parameters
    ----------
    parent  : parent Tk window
    meeting : the matching GroupMeeting

    After ``parent.wait_window(dialog.top)`` resolves, read:
      dialog.user_choice  →  "join"  |  "new_appt"
    """

    def __init__(self, parent: tk.Tk, meeting: GroupMeeting) -> None:
        self.user_choice: str = "new_appt"

        self.top = tk.Toplevel(parent)
        self.top.title("Group Meeting Found")
        self.top.configure(bg=_CANVAS)
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.top.grab_set()

        parent.update_idletasks()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        w, h = 420, 320
        self.top.geometry(f"{w}x{h}+{px + (pw - w)//2}+{py + (ph - h)//2}")

        self._meeting = meeting
        self._build()

    def _build(self) -> None:
        root = self.top

        # ── Title ──────────────────────────────────────────────────
        title_bar = tk.Frame(root, bg=_CANVAS)
        title_bar.pack(fill="x", padx=24, pady=(20, 4))
        tk.Label(
            title_bar, text="📢  Group Meeting Found",
            bg=_CANVAS, fg=_INK, font=("Segoe UI", 12, "bold"),
        ).pack(side="left")

        ttk.Separator(root, orient="horizontal").pack(fill="x", padx=24, pady=(4, 16))

        # ── Info card ─────────────────────────────────────────────
        card = tk.Frame(root, bg=_INFO_BG)
        card.pack(fill="x", padx=24, pady=(0, 16))
        inner = tk.Frame(card, bg=_INFO_BG)
        inner.pack(fill="x", padx=14, pady=12)

        tk.Label(
            inner, text="A group meeting with the same name and duration exists:",
            bg=_INFO_BG, fg=_INFO_FG, font=("Segoe UI", 9),
            wraplength=360, justify="left",
        ).pack(anchor="w")

        gm = self._meeting
        tk.Label(
            inner, text=f'"{gm.name}"',
            bg=_INFO_BG, fg=_INK, font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(4, 0))

        time_str = (
            f"{gm.start_time.strftime('%Y-%m-%d  %H:%M')} – "
            f"{gm.end_time.strftime('%H:%M')}  "
            f"({gm.duration} min)"
        )
        tk.Label(
            inner, text=time_str,
            bg=_INFO_BG, fg=_INFO_FG, font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(2, 0))

        # Participant count
        n = len(gm.participants)
        p_label = f"{n} participant{'s' if n != 1 else ''} already in this meeting"
        tk.Label(
            inner, text=f"👥 {p_label}",
            bg=_INFO_BG, fg=_MUTED, font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(4, 0))

        # ── Question ───────────────────────────────────────────────
        tk.Label(
            root, text="Would you like to join this group meeting?",
            bg=_CANVAS, fg=_BODY, font=("Segoe UI", 10),
        ).pack(padx=24, anchor="w")

        # ── Buttons ────────────────────────────────────────────────
        ttk.Separator(root, orient="horizontal").pack(fill="x", padx=24, pady=(12, 0))
        btn_row = tk.Frame(root, bg=_CANVAS)
        btn_row.pack(fill="x", padx=24, pady=(12, 20))

        tk.Button(
            btn_row, text="No, New Appt",
            bg=_SOFT, fg=_BODY, bd=0, cursor="hand2",
            font=("Segoe UI", 10), padx=16, pady=7,
            activebackground=_HAIRLINE, relief="flat",
            command=self._new_appt,
        ).pack(side="left")

        tk.Button(
            btn_row, text="Join  →",
            bg=_ACCENT, fg="white", bd=0, cursor="hand2",
            font=("Segoe UI", 10, "bold"), padx=16, pady=7,
            activebackground="#2563EB", activeforeground="white",
            relief="flat",
            command=self._join,
        ).pack(side="right")

    def _new_appt(self) -> None:
        self.user_choice = "new_appt"
        self.top.destroy()

    def _join(self) -> None:
        self.user_choice = "join"
        self.top.destroy()
