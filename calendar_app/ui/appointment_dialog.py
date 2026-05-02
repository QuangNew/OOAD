from __future__ import annotations

import tkinter as tk
from datetime import date, datetime
from tkinter import messagebox, ttk
from typing import Callable


_INK = "#111111"
_CANVAS = "#FFFFFF"
_SOFT = "#F8F9FA"
_HAIRLINE = "#E5E7EB"
_MUTED = "#6B7280"
_BODY = "#374151"
_ACCENT = "#3B82F6"
_DANGER = "#EF4444"


class AppointmentDialog:
    def __init__(
        self,
        parent: tk.Tk,
        default_date: date,
        on_submit: Callable[[dict], None],
        mode: str = "add",
        initial_data: dict | None = None,
    ) -> None:
        self._on_submit = on_submit
        self._mode = mode
        self._initial_data = initial_data or {}

        self.top = tk.Toplevel(parent)
        self.top.title("Edit Appointment" if mode == "edit" else "Add New Appointment")
        self.top.configure(bg=_CANVAS)
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.top.grab_set()

        parent.update_idletasks()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        width, height = 500, 620
        self.top.geometry(f"{width}x{height}+{px + (pw - width)//2}+{py + (ph - height)//2}")

        self._default_date = default_date
        self._build()

    def _build(self) -> None:
        title_text = "Edit Appointment" if self._mode == "edit" else "Add New Appointment"
        submit_text = "Save Changes" if self._mode == "edit" else "Add"

        start_dt = self._initial_data.get("start")
        end_dt = self._initial_data.get("end")
        date_text = self._default_date.strftime("%Y-%m-%d")
        if isinstance(start_dt, datetime):
            date_text = start_dt.strftime("%Y-%m-%d")

        is_group = bool(self._initial_data.get("is_group_meeting", False))
        participant_ids = self._initial_data.get("participant_ids", [])
        include_current_user = bool(self._initial_data.get("include_current_user", True))

        title_bar = tk.Frame(self.top, bg=_CANVAS)
        title_bar.pack(fill="x", padx=24, pady=(20, 4))
        tk.Label(
            title_bar,
            text=title_text,
            bg=_CANVAS,
            fg=_INK,
            font=("Segoe UI", 13, "bold"),
        ).pack(side="left")
        tk.Button(
            title_bar,
            text="x",
            bg=_CANVAS,
            fg=_MUTED,
            bd=0,
            font=("Segoe UI", 12),
            cursor="hand2",
            activebackground=_SOFT,
            activeforeground=_INK,
            command=self.top.destroy,
        ).pack(side="right")

        ttk.Separator(self.top, orient="horizontal").pack(fill="x", padx=24, pady=(4, 16))

        body = tk.Frame(self.top, bg=_CANVAS)
        body.pack(fill="both", expand=True, padx=24)

        def _label(text: str, required: bool = False) -> None:
            row = tk.Frame(body, bg=_CANVAS)
            row.pack(fill="x", pady=(0, 2))
            tk.Label(
                row,
                text=text,
                bg=_CANVAS,
                fg=_BODY,
                font=("Segoe UI", 9, "bold"),
            ).pack(side="left")
            if required:
                tk.Label(
                    row,
                    text=" *",
                    bg=_CANVAS,
                    fg=_DANGER,
                    font=("Segoe UI", 9, "bold"),
                ).pack(side="left")

        _label("Appointment Type")
        type_row = tk.Frame(body, bg=_CANVAS)
        type_row.pack(fill="x", pady=(0, 12))

        self._var_type = tk.StringVar(value="group" if is_group else "personal")
        radio_state = "disabled" if self._mode == "edit" else "normal"
        tk.Radiobutton(
            type_row,
            text="Personal appointment",
            variable=self._var_type,
            value="personal",
            state=radio_state,
            bg=_CANVAS,
            fg=_BODY,
            activebackground=_CANVAS,
            selectcolor=_CANVAS,
            command=self._toggle_group_fields,
            font=("Segoe UI", 10),
        ).pack(side="left")
        tk.Radiobutton(
            type_row,
            text="Group meeting",
            variable=self._var_type,
            value="group",
            state=radio_state,
            bg=_CANVAS,
            fg=_BODY,
            activebackground=_CANVAS,
            selectcolor=_CANVAS,
            command=self._toggle_group_fields,
            font=("Segoe UI", 10),
        ).pack(side="left", padx=(12, 0))

        _label("Appointment Name", required=True)
        self._var_name = tk.StringVar(value=self._initial_data.get("name", ""))
        ttk.Entry(body, textvariable=self._var_name, font=("Segoe UI", 10)).pack(
            fill="x", pady=(0, 12), ipady=4
        )

        _label("Location")
        self._var_location = tk.StringVar(value=self._initial_data.get("location", ""))
        ttk.Entry(body, textvariable=self._var_location, font=("Segoe UI", 10)).pack(
            fill="x", pady=(0, 12), ipady=4
        )

        _label("Start  (YYYY-MM-DD  HH:MM)", required=True)
        start_row = tk.Frame(body, bg=_CANVAS)
        start_row.pack(fill="x", pady=(0, 12))
        self._var_start_date = tk.StringVar(
            value=start_dt.strftime("%Y-%m-%d") if isinstance(start_dt, datetime) else date_text,
        )
        self._var_start_time = tk.StringVar(
            value=start_dt.strftime("%H:%M") if isinstance(start_dt, datetime) else "09:00",
        )
        ttk.Entry(start_row, textvariable=self._var_start_date, font=("Segoe UI", 10), width=14).pack(
            side="left", ipady=4
        )
        tk.Label(start_row, text="  ", bg=_CANVAS).pack(side="left")
        ttk.Entry(start_row, textvariable=self._var_start_time, font=("Segoe UI", 10), width=8).pack(
            side="left", ipady=4
        )

        _label("End  (YYYY-MM-DD  HH:MM)", required=True)
        end_row = tk.Frame(body, bg=_CANVAS)
        end_row.pack(fill="x", pady=(0, 12))
        self._var_end_date = tk.StringVar(
            value=end_dt.strftime("%Y-%m-%d") if isinstance(end_dt, datetime) else date_text,
        )
        self._var_end_time = tk.StringVar(
            value=end_dt.strftime("%H:%M") if isinstance(end_dt, datetime) else "10:00",
        )
        ttk.Entry(end_row, textvariable=self._var_end_date, font=("Segoe UI", 10), width=14).pack(
            side="left", ipady=4
        )
        tk.Label(end_row, text="  ", bg=_CANVAS).pack(side="left")
        ttk.Entry(end_row, textvariable=self._var_end_time, font=("Segoe UI", 10), width=8).pack(
            side="left", ipady=4
        )

        self._group_frame = tk.Frame(body, bg=_CANVAS)
        self._group_frame.pack(fill="x", pady=(0, 8))
        tk.Label(
            self._group_frame,
            text="Use comma-separated user IDs for other participants.",
            bg=_CANVAS,
            fg=_MUTED,
            font=("Segoe UI", 9),
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=(0, 6))

        group_label_row = tk.Frame(self._group_frame, bg=_CANVAS)
        group_label_row.pack(fill="x", pady=(0, 2))
        tk.Label(
            group_label_row,
            text="Other Participant IDs",
            bg=_CANVAS,
            fg=_BODY,
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left")

        self._var_participants = tk.StringVar(value=", ".join(participant_ids))
        ttk.Entry(self._group_frame, textvariable=self._var_participants, font=("Segoe UI", 10)).pack(
            fill="x", ipady=4
        )

        self._var_include_current_user = tk.BooleanVar(value=include_current_user)
        self._include_current_user_check = tk.Checkbutton(
            self._group_frame,
            text="Join this meeting now",
            variable=self._var_include_current_user,
            bg=_CANVAS,
            fg=_BODY,
            activebackground=_CANVAS,
            font=("Segoe UI", 10),
        )
        self._include_current_user_check.pack(anchor="w", pady=(8, 0))
        if self._mode == "edit" and is_group:
            self._include_current_user_check.configure(state="disabled")

        self._var_reminder_enabled = tk.BooleanVar(value=bool(self._initial_data.get("reminder_msg", "")))
        tk.Checkbutton(
            body,
            text="Add Reminder",
            variable=self._var_reminder_enabled,
            bg=_CANVAS,
            fg=_BODY,
            activebackground=_CANVAS,
            font=("Segoe UI", 10),
            command=self._toggle_reminder,
        ).pack(anchor="w", pady=(4, 6))

        self._reminder_frame = tk.Frame(body, bg=_CANVAS)
        self._reminder_frame.pack(fill="x")
        tk.Label(
            self._reminder_frame,
            text="Message",
            bg=_CANVAS,
            fg=_MUTED,
            font=("Segoe UI", 9),
        ).pack(anchor="w")
        self._var_reminder_msg = tk.StringVar(value=self._initial_data.get("reminder_msg", ""))
        ttk.Entry(self._reminder_frame, textvariable=self._var_reminder_msg, font=("Segoe UI", 10)).pack(
            fill="x", ipady=4
        )

        ttk.Separator(self.top, orient="horizontal").pack(fill="x", padx=24, pady=(12, 0))
        button_row = tk.Frame(self.top, bg=_CANVAS)
        button_row.pack(fill="x", padx=24, pady=(12, 20))

        tk.Button(
            button_row,
            text="Cancel",
            bg=_SOFT,
            fg=_BODY,
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 10),
            padx=16,
            pady=7,
            relief="flat",
            activebackground=_HAIRLINE,
            command=self.top.destroy,
        ).pack(side="left")

        tk.Button(
            button_row,
            text=submit_text,
            bg=_ACCENT,
            fg="white",
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=16,
            pady=7,
            relief="flat",
            activebackground="#2563EB",
            command=self._submit,
        ).pack(side="right")

        self._toggle_group_fields()
        self._toggle_reminder()

    def _toggle_group_fields(self) -> None:
        if self._var_type.get() == "group":
            self._group_frame.pack(fill="x", pady=(0, 8))
        else:
            self._group_frame.pack_forget()

    def _toggle_reminder(self) -> None:
        if self._var_reminder_enabled.get():
            self._reminder_frame.pack(fill="x")
        else:
            self._reminder_frame.pack_forget()

    def _submit(self) -> None:
        name = self._var_name.get().strip()
        location = self._var_location.get().strip()

        if not name:
            messagebox.showerror("Validation Error", "Appointment name cannot be empty.", parent=self.top)
            return

        try:
            start = datetime.strptime(
                f"{self._var_start_date.get().strip()} {self._var_start_time.get().strip()}",
                "%Y-%m-%d %H:%M",
            )
        except ValueError:
            messagebox.showerror(
                "Validation Error",
                "Start date/time format must be YYYY-MM-DD and HH:MM.",
                parent=self.top,
            )
            return

        try:
            end = datetime.strptime(
                f"{self._var_end_date.get().strip()} {self._var_end_time.get().strip()}",
                "%Y-%m-%d %H:%M",
            )
        except ValueError:
            messagebox.showerror(
                "Validation Error",
                "End date/time format must be YYYY-MM-DD and HH:MM.",
                parent=self.top,
            )
            return

        if end <= start:
            messagebox.showerror("Validation Error", "End time must be after start time.", parent=self.top)
            return

        is_group_meeting = self._var_type.get() == "group"
        participant_ids: list[str] = []
        include_current_user = True
        if is_group_meeting:
            participant_ids = [
                participant.strip()
                for participant in self._var_participants.get().split(",")
                if participant.strip()
            ]
            include_current_user = bool(self._var_include_current_user.get())

        reminder_msg = self._var_reminder_msg.get().strip() if self._var_reminder_enabled.get() else ""

        self.top.destroy()
        self._on_submit(
            {
                "name": name,
                "location": location,
                "start": start,
                "end": end,
                "reminder_msg": reminder_msg,
                "is_group_meeting": is_group_meeting,
                "participant_ids": participant_ids,
                "include_current_user": include_current_user,
            }
        )
