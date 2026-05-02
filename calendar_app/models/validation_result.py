from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.appointment import Appointment
    from models.group_meeting import GroupMeeting


@dataclass
class ValidationResult:
    """Data-transfer object returned by AppointmentController to CalendarUI."""
    is_valid: bool
    error_message: str = ""
    conflict_appointment: "Appointment | None" = None
    matched_group_meeting: "GroupMeeting | None" = None
