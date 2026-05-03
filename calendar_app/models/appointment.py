from __future__ import annotations
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from models.reminder import Reminder

if TYPE_CHECKING:
    pass


class Appointment:
    """
    Core domain entity representing a calendar appointment.

    The ``duration`` attribute is derived (computed on demand) from
    ``start_time`` and ``end_time``, matching the /duration notation in the
    Class Diagram.
    """

    def __init__(
        self,
        appointment_id: str,
        name: str,
        location: str,
        start_time: datetime,
        end_time: datetime,
        owner_user_id: str | None = None,
    ) -> None:
        self.appointment_id: str = appointment_id
        self.name: str = name
        self.location: str = location
        self.start_time: datetime = start_time
        self.end_time: datetime = end_time
        self.owner_user_id: str | None = owner_user_id
        self.reminders: list[Reminder] = []
        self.is_group_meeting: bool = False

    # ------------------------------------------------------------------
    # Derived attribute  (maps to  +/ duration: int  in Class Diagram)
    # ------------------------------------------------------------------

    @property
    def duration(self) -> int:
        """Return duration in whole minutes."""
        return int((self.end_time - self.start_time).total_seconds() // 60)

    def calculate_duration(self) -> int:
        """Explicit method alias required by Class Diagram interface."""
        return self.duration

    # ------------------------------------------------------------------
    # Reminder management
    # ------------------------------------------------------------------

    def add_reminder(self, rem: Reminder) -> None:
        self.reminders.append(rem)

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        name: str,
        location: str,
        start_time: datetime,
        end_time: datetime,
        owner_user_id: str | None = None,
    ) -> "Appointment":
        return cls(str(uuid.uuid4()), name, location, start_time, end_time, owner_user_id=owner_user_id)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"Appointment({self.name!r}, "
            f"{self.start_time.strftime('%Y-%m-%d %H:%M')}–"
            f"{self.end_time.strftime('%H:%M')})"
        )
