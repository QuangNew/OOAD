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
from workflow_log import workflow_log


def main() -> None:
    workflow_log("App", "Start application")
    auth = AuthUI()
    workflow_log("App", "Open authentication window")
    user = auth.run()
    if user is None:
        workflow_log("App", "Authentication cancelled")
        return

    workflow_log("App", "Authentication completed", f"user_id={user.user_id}")
    calendar = Calendar(calendar_id="cal-001")
    items = FileStorage.load_calendar_items_for_user(user.user_id)
    workflow_log("App", "Load visible calendar items", f"count={len(items)}")
    for appt in items:
        calendar.add_appointment(appt)

    startup_warnings = FileStorage.consume_warnings()
    if startup_warnings:
        workflow_log("App", "Collected startup load warnings", f"count={len(startup_warnings)}")

    controller = AppointmentController(calendar=calendar, user=user)
    workflow_log("App", "Wire controller and main UI")
    app = CalendarUI(
        controller=controller,
        user=user,
        startup_warnings=startup_warnings,
    )
    workflow_log("App", "Start Tkinter event loop")
    app.run()
    workflow_log("App", "Application closed")


if __name__ == "__main__":
    main()
