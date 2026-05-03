"""
Entry point for the Calendar Appointment application.

Run from the calendar_app/ directory:
    python main.py

Or from the project root:
    python calendar_app/main.py
"""
from __future__ import annotations
import os
import sys

# Ensure calendar_app/ is on sys.path so all package imports resolve
# regardless of where the script is invoked from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage.file_storage import FileStorage
from models.calendar import Calendar
from controller.appointment_controller import AppointmentController
from ui.auth_ui import AuthUI
from ui.calendar_ui import CalendarUI


def main() -> None:
    auth = AuthUI()
    user = auth.run()
    if user is None:
        return

    # ── Bootstrap calendar ─────────────────────────────────────────
    calendar = Calendar(calendar_id="cal-001")
    for appt in FileStorage.load_calendar_items_for_user(user.user_id):
        calendar.add_appointment(appt)

    startup_warnings = FileStorage.consume_warnings()

    # ── Wire controller + UI ───────────────────────────────────────
    controller = AppointmentController(calendar=calendar, user=user)
    app = CalendarUI(
        controller=controller,
        user=user,
        startup_warnings=startup_warnings,
    )
    app.run()


if __name__ == "__main__":
    main()
