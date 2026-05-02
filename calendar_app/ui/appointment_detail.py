from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from models.group_meeting import GroupMeeting


_INK = "#111111"
_CANVAS = "#FFFFFF"
_SOFT = "#F8F9FA"
_CARD = "#F5F5F5"
_MUTED = "#6B7280"
_BODY = "#374151"
_ACCENT = "#3B82F6"
_DANGER = "#EF4444"


class AppointmentDetailDialog:
    def __init__(self, parent: tk.Tk, appointment) -> None:
        self.action = "close"
        self.top = tk.Toplevel(parent)
        self.top.title("Appointment Details")
        self.top.configure(bg=_CANVAS)
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.top.grab_set()

        parent.update_idletasks()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        width, height = 460, 360
        self.top.geometry(f"{width}x{height}+{px + (pw - width)//2}+{py + (ph - height)//2}")

        self._appointment = appointment
        self._build()

    def _build(self) -> None:
        appointment = self._appointment

        title_bar = tk.Frame(self.top, bg=_CANVAS)
        title_bar.pack(fill="x", padx=24, pady=(20, 4))
        tk.Label(
            title_bar,
            text="Appointment Details",
            bg=_CANVAS,
            fg=_INK,
            font=("Segoe UI", 13, "bold"),
        ).pack(side="left")

        ttk.Separator(self.top, orient="horizontal").pack(fill="x", padx=24, pady=(4, 16))

        card = tk.Frame(self.top, bg=_CARD)
        card.pack(fill="both", expand=True, padx=24)
        body = tk.Frame(card, bg=_CARD)
        body.pack(fill="both", expand=True, padx=18, pady=16)

        tk.Label(
            body,
            text=appointment.name,
            bg=_CARD,
            fg=_INK,
            font=("Segoe UI", 14, "bold"),
            wraplength=380,
            justify="left",
        ).pack(anchor="w")

        tk.Label(
            body,
            text=(
                f"{appointment.start_time.strftime('%A, %d %B %Y')}\n"
                f"{appointment.start_time.strftime('%H:%M')} - "
                f"{appointment.end_time.strftime('%H:%M')}  ({appointment.duration} min)"
            ),
            bg=_CARD,
            fg=_BODY,
            font=("Segoe UI", 10),
            justify="left",
        ).pack(anchor="w", pady=(10, 0))

        tk.Label(
            body,
            text=f"Location: {appointment.location or 'Not specified'}",
            bg=_CARD,
            fg=_BODY,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(10, 0))

        tk.Label(
            body,
            text=f"Type: {'Group meeting' if isinstance(appointment, GroupMeeting) else 'Personal appointment'}",
            bg=_CARD,
            fg=_BODY,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(10, 0))

        if isinstance(appointment, GroupMeeting):
            participants_text = ", ".join(appointment.participants) if appointment.participants else "No participants"
            tk.Label(
                body,
                text=f"Participants: {participants_text}",
                bg=_CARD,
                fg=_ACCENT,
                font=("Segoe UI", 10),
                wraplength=380,
                justify="left",
            ).pack(anchor="w", pady=(10, 0))

        reminder_text = appointment.reminders[0].message if appointment.reminders else "No reminder"
        tk.Label(
            body,
            text=f"Reminder: {reminder_text}",
            bg=_CARD,
            fg=_MUTED,
            font=("Segoe UI", 10),
            wraplength=380,
            justify="left",
        ).pack(anchor="w", pady=(10, 0))

        ttk.Separator(self.top, orient="horizontal").pack(fill="x", padx=24, pady=(14, 0))
        button_row = tk.Frame(self.top, bg=_CANVAS)
        button_row.pack(fill="x", padx=24, pady=(12, 20))

        tk.Button(
            button_row,
            text="Close",
            bg=_SOFT,
            fg=_BODY,
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 10),
            padx=16,
            pady=7,
            relief="flat",
            command=self.top.destroy,
        ).pack(side="left")

        tk.Button(
            button_row,
            text="Delete",
            bg=_DANGER,
            fg="white",
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=16,
            pady=7,
            relief="flat",
            command=self._delete,
        ).pack(side="right")

        tk.Button(
            button_row,
            text="Edit",
            bg=_ACCENT,
            fg="white",
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=16,
            pady=7,
            relief="flat",
            command=self._edit,
        ).pack(side="right", padx=(0, 8))

    def _edit(self) -> None:
        self.action = "edit"
        self.top.destroy()

    def _delete(self) -> None:
        self.action = "delete"
        self.top.destroy()