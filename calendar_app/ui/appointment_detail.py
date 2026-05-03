from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from models.group_meeting import GroupMeeting
from ui.dialog_layout import ScrollableDialogLayout


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
        self.top.transient(parent)
        self.top.grab_set()

        self._layout = ScrollableDialogLayout(
            parent,
            self.top,
            width=520,
            height=460,
            min_width=420,
            min_height=320,
            bg=_CANVAS,
        )

        self._appointment = appointment
        self._build()

    def _build(self) -> None:
        appointment = self._appointment

        title_bar = self._layout.header
        tk.Label(
            title_bar,
            text="Appointment Details",
            bg=_CANVAS,
            fg=_INK,
            font=("Segoe UI", 13, "bold"),
        ).pack(side="left")

        card = tk.Frame(self._layout.body, bg=_CARD)
        card.pack(fill="x")
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

        button_row = self._layout.footer
        button_row.grid_columnconfigure(1, weight=1)

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
        ).grid(row=0, column=0, sticky="w")

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
        ).grid(row=0, column=3, sticky="e")

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
        ).grid(row=0, column=2, sticky="e", padx=(0, 8))

    def _edit(self) -> None:
        self.action = "edit"
        self.top.destroy()

    def _delete(self) -> None:
        self.action = "delete"
        self.top.destroy()