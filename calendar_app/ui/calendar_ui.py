from __future__ import annotations

import calendar as cal_lib
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

from models.group_meeting import GroupMeeting

if TYPE_CHECKING:
    from controller.appointment_controller import AppointmentController
    from models.user import User


_INK = "#111111"
_CANVAS = "#FFFFFF"
_SOFT = "#F8F9FA"
_CARD = "#F5F5F5"
_HAIRLINE = "#E5E7EB"
_MUTED = "#6B7280"
_BODY = "#374151"
_ACCENT = "#3B82F6"
_DANGER = "#EF4444"
_TODAY_BG = "#EFF6FF"
_TODAY_FG = _ACCENT
_WARN_BG = "#FEF3C7"
_WARN_FG = "#92400E"


class CalendarUI:
    def __init__(
        self,
        controller: "AppointmentController",
        user: "User",
        startup_warnings: list[str] | None = None,
    ) -> None:
        self.controller = controller
        self.user = user
        self._startup_warnings = startup_warnings or []

        self.active_date: date = date.today()
        self.view_year: int = date.today().year
        self.view_month: int = date.today().month

        self.root = tk.Tk()
        self.root.title("Calendar App")
        self.root.geometry("980x680")
        self.root.minsize(860, 600)
        self.root.configure(bg=_CANVAS)

        self._setup_styles()
        self._build_layout()
        self._render_calendar()
        self._render_appointments()

    def _setup_styles(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", background=_CANVAS, foreground=_INK, font=("Segoe UI", 10))
        style.configure("TFrame", background=_CANVAS)
        style.configure("TLabel", background=_CANVAS, foreground=_INK)
        style.configure("TSeparator", background=_HAIRLINE)
        style.configure("TEntry", fieldbackground=_CANVAS, bordercolor=_HAIRLINE, relief="flat")
        style.map("TEntry", bordercolor=[("focus", _ACCENT), ("!focus", _HAIRLINE)])

    def _build_layout(self) -> None:
        main = tk.Frame(self.root, bg=_CANVAS)
        main.pack(fill="both", expand=True, padx=24, pady=18)

        header = tk.Frame(main, bg=_CANVAS)
        header.pack(fill="x", pady=(0, 10))
        tk.Label(
            header,
            text="Calendar Appointment Manager",
            bg=_CANVAS,
            fg=_INK,
            font=("Segoe UI", 15, "bold"),
        ).pack(side="left")
        tk.Label(
            header,
            text=(
                f"User: {self.user.full_name}"
                if not self.user.username
                else f"User: {self.user.full_name} (@{self.user.username})"
            ),
            bg=_CANVAS,
            fg=_MUTED,
            font=("Segoe UI", 9),
        ).pack(side="right", pady=4)

        ttk.Separator(main, orient="horizontal").pack(fill="x", pady=(0, 14))

        if self._startup_warnings:
            warning_bar = tk.Frame(main, bg=_WARN_BG)
            warning_bar.pack(fill="x", pady=(0, 12))
            tk.Label(
                warning_bar,
                text=f"Some data files were skipped during loading ({len(self._startup_warnings)} issue(s)).",
                bg=_WARN_BG,
                fg=_WARN_FG,
                font=("Segoe UI", 9, "bold"),
            ).pack(side="left", padx=12, pady=8)
            tk.Button(
                warning_bar,
                text="Details",
                bg=_WARN_BG,
                fg=_WARN_FG,
                bd=0,
                cursor="hand2",
                font=("Segoe UI", 9, "underline"),
                activebackground=_WARN_BG,
                activeforeground=_WARN_FG,
                command=self._show_load_warnings,
            ).pack(side="right", padx=(0, 12))

        content = tk.Frame(main, bg=_CANVAS)
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=0, minsize=300)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        self._left = tk.Frame(content, bg=_CANVAS)
        self._right = tk.Frame(content, bg=_CANVAS)
        self._left.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        self._right.grid(row=0, column=1, sticky="nsew")

        self._build_calendar_panel()
        self._build_appointments_panel()

    def _build_calendar_panel(self) -> None:
        nav = tk.Frame(self._left, bg=_CANVAS)
        nav.pack(fill="x", pady=(0, 8))
        tk.Button(
            nav,
            text="<",
            bg=_CANVAS,
            fg=_INK,
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 12),
            activebackground=_SOFT,
            command=self._prev_month,
        ).pack(side="left")
        self._month_label = tk.Label(
            nav,
            text="",
            bg=_CANVAS,
            fg=_INK,
            font=("Segoe UI", 12, "bold"),
        )
        self._month_label.pack(side="left", expand=True)
        tk.Button(
            nav,
            text=">",
            bg=_CANVAS,
            fg=_INK,
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 12),
            activebackground=_SOFT,
            command=self._next_month,
        ).pack(side="right")

        header = tk.Frame(self._left, bg=_CANVAS)
        header.pack(fill="x")
        for column, name in enumerate(["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]):
            tk.Label(
                header,
                text=name,
                bg=_CANVAS,
                fg=_MUTED,
                font=("Segoe UI", 9, "bold"),
                width=4,
            ).grid(row=0, column=column, padx=1, pady=(0, 4))

        self._grid_frame = tk.Frame(self._left, bg=_CANVAS)
        self._grid_frame.pack(fill="x")

        tk.Button(
            self._left,
            text="+ Add Appointment / Group Meeting",
            bg=_ACCENT,
            fg="white",
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=8,
            relief="flat",
            activebackground="#2563EB",
            command=self._open_add_appointment,
        ).pack(fill="x", pady=(18, 0))

        tk.Label(
            self._left,
            text="Tip: open Details or click a card to inspect and edit it.",
            bg=_CANVAS,
            fg=_MUTED,
            font=("Segoe UI", 9),
            wraplength=260,
            justify="left",
        ).pack(fill="x", pady=(10, 0))

    def _build_appointments_panel(self) -> None:
        self._appt_header = tk.Label(
            self._right,
            text="Appointments",
            bg=_CANVAS,
            fg=_INK,
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        )
        self._appt_header.pack(fill="x", pady=(0, 6))

        ttk.Separator(self._right, orient="horizontal").pack(fill="x", pady=(0, 10))

        outer = tk.Frame(self._right, bg=_CANVAS)
        outer.pack(fill="both", expand=True)
        self._scroll_canvas = tk.Canvas(outer, bg=_CANVAS, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=self._scroll_canvas.yview)
        self._scroll_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self._scroll_canvas.pack(side="left", fill="both", expand=True)

        self._list_frame = tk.Frame(self._scroll_canvas, bg=_CANVAS)
        self._canvas_window = self._scroll_canvas.create_window((0, 0), window=self._list_frame, anchor="nw")

        self._list_frame.bind("<Configure>", self._on_frame_configure)
        self._scroll_canvas.bind("<Configure>", self._on_canvas_configure)
        self._scroll_canvas.bind("<MouseWheel>", self._on_mousewheel)

    def _on_frame_configure(self, _: tk.Event) -> None:
        self._scroll_canvas.configure(scrollregion=self._scroll_canvas.bbox("all"))

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self._scroll_canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event: tk.Event) -> None:
        self._scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _render_calendar(self) -> None:
        for widget in self._grid_frame.winfo_children():
            widget.destroy()

        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]
        self._month_label.config(text=f"{month_names[self.view_month - 1]} {self.view_year}")

        today = date.today()
        item_dates = {item.start_time.date() for item in self.controller.current_calendar.get_all()}

        for row_index, week in enumerate(cal_lib.monthcalendar(self.view_year, self.view_month)):
            for column_index, day in enumerate(week):
                if day == 0:
                    tk.Label(self._grid_frame, text="", width=4, bg=_CANVAS).grid(
                        row=row_index, column=column_index, padx=1, pady=1
                    )
                    continue

                cell_date = date(self.view_year, self.view_month, day)
                is_today = cell_date == today
                is_selected = cell_date == self.active_date
                has_items = cell_date in item_dates

                if is_selected:
                    bg, fg, weight = _ACCENT, "white", "bold"
                elif is_today:
                    bg, fg, weight = _TODAY_BG, _TODAY_FG, "bold"
                else:
                    bg, fg, weight = _CANVAS, _INK, "normal"

                label = f"{day}*" if has_items and not is_selected else str(day)
                tk.Button(
                    self._grid_frame,
                    text=label,
                    bg=bg,
                    fg=fg,
                    bd=0,
                    cursor="hand2",
                    font=("Segoe UI", 10, weight),
                    width=4,
                    pady=5,
                    relief="flat",
                    activebackground=_SOFT,
                    command=lambda selected=cell_date: self._select_date(selected),
                ).grid(row=row_index, column=column_index, padx=1, pady=1)

    def _render_appointments(self) -> None:
        for widget in self._list_frame.winfo_children():
            widget.destroy()

        self._appt_header.config(text=f"Appointments - {self.active_date.strftime('%B %d, %Y')}")
        appointments = sorted(
            self.controller.current_calendar.get_appointments_on_date(self.active_date),
            key=lambda item: item.start_time,
        )

        if not appointments:
            tk.Label(
                self._list_frame,
                text="No appointments on this day.",
                bg=_CANVAS,
                fg=_MUTED,
                font=("Segoe UI", 10),
                pady=24,
            ).pack(fill="x")
            return

        for appointment in appointments:
            self._render_card(appointment)

    def _render_card(self, appointment) -> None:
        outer = tk.Frame(self._list_frame, bg=_HAIRLINE)
        outer.pack(fill="x", pady=(0, 8))
        card = tk.Frame(outer, bg=_CARD)
        card.pack(fill="x", padx=1, pady=1)
        body = tk.Frame(card, bg=_CARD)
        body.pack(fill="x", padx=14, pady=10)

        clickable_widgets = [outer, card, body]

        time_label = tk.Label(
            body,
            text=(
                f"{appointment.start_time.strftime('%H:%M')} - "
                f"{appointment.end_time.strftime('%H:%M')}  ({appointment.duration} min)"
            ),
            bg=_CARD,
            fg=_MUTED,
            font=("Segoe UI", 9),
        )
        time_label.pack(anchor="w")
        clickable_widgets.append(time_label)

        name_label = tk.Label(
            body,
            text=appointment.name,
            bg=_CARD,
            fg=_INK,
            font=("Segoe UI", 11, "bold"),
            wraplength=380,
            justify="left",
        )
        name_label.pack(anchor="w", pady=(3, 0))
        clickable_widgets.append(name_label)

        if appointment.location:
            location_label = tk.Label(
                body,
                text=f"Location: {appointment.location}",
                bg=_CARD,
                fg=_BODY,
                font=("Segoe UI", 9),
            )
            location_label.pack(anchor="w", pady=(2, 0))
            clickable_widgets.append(location_label)

        if isinstance(appointment, GroupMeeting):
            group_label = tk.Label(
                body,
                text=f"Group meeting - {len(appointment.participants)} participant(s)",
                bg=_CARD,
                fg=_ACCENT,
                font=("Segoe UI", 9),
            )
            group_label.pack(anchor="w", pady=(3, 0))
            clickable_widgets.append(group_label)

        if appointment.reminders:
            reminder_label = tk.Label(
                body,
                text=f"Reminder: {appointment.reminders[0].message}",
                bg=_CARD,
                fg=_MUTED,
                font=("Segoe UI", 9),
                wraplength=380,
                justify="left",
            )
            reminder_label.pack(anchor="w", pady=(2, 0))
            clickable_widgets.append(reminder_label)

        footer = tk.Frame(body, bg=_CARD)
        footer.pack(fill="x", pady=(8, 0))
        tk.Button(
            footer,
            text="Details",
            bg=_CARD,
            fg=_ACCENT,
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 9, "underline"),
            activebackground=_CARD,
            activeforeground="#2563EB",
            relief="flat",
            command=lambda appt=appointment: self._open_appointment_detail(appt),
        ).pack(side="left")
        tk.Button(
            footer,
            text="Edit",
            bg=_CARD,
            fg=_BODY,
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 9),
            activebackground=_CARD,
            relief="flat",
            command=lambda appt=appointment: self._open_edit_dialog(appt),
        ).pack(side="right")
        tk.Button(
            footer,
            text="Delete",
            bg=_CARD,
            fg=_DANGER,
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 9),
            activebackground=_CARD,
            activeforeground="#DC2626",
            relief="flat",
            command=lambda appt=appointment: self._confirm_delete(appt),
        ).pack(side="right", padx=(0, 8))

        for widget in clickable_widgets:
            widget.bind("<Button-1>", lambda _event, appt=appointment: self._open_appointment_detail(appt))

    def _prev_month(self) -> None:
        if self.view_month == 1:
            self.view_month, self.view_year = 12, self.view_year - 1
        else:
            self.view_month -= 1
        self._render_calendar()

    def _next_month(self) -> None:
        if self.view_month == 12:
            self.view_month, self.view_year = 1, self.view_year + 1
        else:
            self.view_month += 1
        self._render_calendar()

    def _select_date(self, selected_date: date) -> None:
        self.active_date = selected_date
        self._render_calendar()
        self._render_appointments()

    def _open_add_appointment(self) -> None:
        from ui.appointment_dialog import AppointmentDialog

        AppointmentDialog(self.root, self.active_date, self._on_form_submitted, mode="add")

    def _open_appointment_detail(self, appointment) -> None:
        from ui.appointment_detail import AppointmentDetailDialog

        dialog = AppointmentDetailDialog(self.root, appointment)
        self.root.wait_window(dialog.top)
        if dialog.action == "edit":
            self._open_edit_dialog(appointment)
        elif dialog.action == "delete":
            self._confirm_delete(appointment)

    def _open_edit_dialog(self, appointment) -> None:
        from ui.appointment_dialog import AppointmentDialog

        initial_data = {
            "name": appointment.name,
            "location": appointment.location,
            "start": appointment.start_time,
            "end": appointment.end_time,
            "reminder_msg": appointment.reminders[0].message if appointment.reminders else "",
            "is_group_meeting": isinstance(appointment, GroupMeeting),
            "participant_ids": [
                participant
                for participant in getattr(appointment, "participants", [])
                if participant != self.user.user_id
            ],
            "include_current_user": True,
        }
        AppointmentDialog(
            self.root,
            appointment.start_time.date(),
            lambda form_data, current=appointment: self._on_edit_form_submitted(current, form_data),
            mode="edit",
            initial_data=initial_data,
        )

    def _on_form_submitted(self, form_data: dict) -> None:
        if form_data.get("is_group_meeting"):
            result = self.controller.create_group_meeting(
                name=form_data["name"],
                location=form_data["location"],
                start=form_data["start"],
                end=form_data["end"],
                reminder_msg=form_data["reminder_msg"],
                participant_ids=form_data["participant_ids"],
                include_current_user=form_data["include_current_user"],
            )
            if not result.is_valid:
                messagebox.showerror("Validation Error", result.error_message, parent=self.root)
                return
            if result.conflict_appointment is not None:
                messagebox.showerror(
                    "Conflict",
                    f"This group meeting overlaps with '{result.conflict_appointment.name}'.",
                    parent=self.root,
                )
                return
            self._refresh()
            return

        result = self.controller.handle_add_appointment(
            name=form_data["name"],
            location=form_data["location"],
            start=form_data["start"],
            end=form_data["end"],
            reminder_msg=form_data["reminder_msg"],
        )

        if not result.is_valid:
            messagebox.showerror("Validation Error", result.error_message, parent=self.root)
            return

        if result.conflict_appointment is not None:
            from ui.conflict_dialog import ConflictDialog

            dialog = ConflictDialog(self.root, result.conflict_appointment)
            self.root.wait_window(dialog.top)
            if dialog.user_choice == "replace":
                self.controller.replace_existing_appointment(
                    result.conflict_appointment,
                    form_data["name"],
                    form_data["location"],
                    form_data["start"],
                    form_data["end"],
                    form_data["reminder_msg"],
                )
                self._refresh()
            return

        if result.matched_group_meeting is not None:
            from ui.group_meeting_dialog import GroupMeetingDialog

            dialog = GroupMeetingDialog(self.root, result.matched_group_meeting)
            self.root.wait_window(dialog.top)
            if dialog.user_choice == "join":
                self.controller.join_existing_group_meeting(result.matched_group_meeting)
            else:
                self.controller.force_add_appointment(
                    form_data["name"],
                    form_data["location"],
                    form_data["start"],
                    form_data["end"],
                    form_data["reminder_msg"],
                )
            self._refresh()
            return

        self._refresh()

    def _on_edit_form_submitted(self, existing, form_data: dict) -> None:
        result = self.controller.update_appointment(
            existing,
            name=form_data["name"],
            location=form_data["location"],
            start=form_data["start"],
            end=form_data["end"],
            reminder_msg=form_data["reminder_msg"],
            participant_ids=form_data.get("participant_ids", []),
        )
        if not result.is_valid:
            messagebox.showerror("Validation Error", result.error_message, parent=self.root)
            return
        if result.conflict_appointment is not None:
            messagebox.showerror(
                "Conflict",
                (
                    "The updated time overlaps with "
                    f"'{result.conflict_appointment.name}' "
                    f"({result.conflict_appointment.start_time.strftime('%H:%M')} - "
                    f"{result.conflict_appointment.end_time.strftime('%H:%M')})."
                ),
                parent=self.root,
            )
            return
        self._refresh()

    def _confirm_delete(self, appointment) -> None:
        if messagebox.askyesno(
            "Delete Appointment",
            f"Delete '{appointment.name}'?\nThis action cannot be undone.",
            icon="warning",
            parent=self.root,
        ):
            self.controller.delete_appointment(appointment)
            self._refresh()

    def _show_load_warnings(self) -> None:
        messagebox.showwarning("Load Warnings", "\n".join(self._startup_warnings), parent=self.root)

    def _refresh(self) -> None:
        self._render_calendar()
        self._render_appointments()

    def run(self) -> None:
        self.root.mainloop()
