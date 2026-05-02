from __future__ import annotations
from datetime import date, datetime
from typing import TYPE_CHECKING

from models.appointment import Appointment
from models.group_meeting import GroupMeeting

if TYPE_CHECKING:
    pass


class Calendar:
    """
    In-memory container of all appointments owned by one user.

    Persistence (file I/O) is intentionally NOT handled here;
    the controller calls FileStorage after every mutation to keep
    this class as a pure domain object.
    """

    def __init__(self, calendar_id: str) -> None:
        self.calendar_id: str = calendar_id
        self._appointments: list[Appointment] = []

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_appointment(self, appt: Appointment) -> None:
        self._appointments.append(appt)

    def remove_appointment(self, appt: Appointment) -> None:
        self._appointments = [
            a for a in self._appointments
            if a.appointment_id != appt.appointment_id
        ]

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_appointments_by_time(
        self, start: datetime, end: datetime
    ) -> list[Appointment]:
        """
        Return all appointments that overlap the [start, end) interval.

        Overlap condition:  appt.start < end  AND  appt.end > start
        Back-to-back appointments (appt.end == start) do NOT overlap.
        """
        return [
            a for a in self._appointments
            if a.start_time < end and a.end_time > start
        ]

    def get_group_meetings_by_name_and_duration(
        self, name: str, duration: int
    ) -> list[GroupMeeting]:
        """Return group meetings matching exact name AND duration (minutes)."""
        return [
            a for a in self._appointments
            if isinstance(a, GroupMeeting)
            and a.name == name
            and a.duration == duration
        ]

    def get_appointments_on_date(self, target: date) -> list[Appointment]:
        """Return all appointments whose start date equals target."""
        return [
            a for a in self._appointments
            if a.start_time.date() == target
        ]

    def get_all(self) -> list[Appointment]:
        return list(self._appointments)
