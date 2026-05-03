from __future__ import annotations
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from models.appointment import Appointment

if TYPE_CHECKING:
    from models.user import User


class GroupMeeting(Appointment):
    """
    A group appointment shared among multiple users.

    Inherits all fields and behaviour from Appointment.
    Adds the ``participants`` list (user IDs) as per the Class Diagram
    aggregation  GroupMeeting o-- User.
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
        super().__init__(
            appointment_id,
            name,
            location,
            start_time,
            end_time,
            owner_user_id=owner_user_id,
        )
        self.participants: list[str] = []   # stores userId strings
        self.is_group_meeting = True

    # ------------------------------------------------------------------
    # Participant management
    # ------------------------------------------------------------------

    def add_participant(self, user: "User") -> None:
        if user.user_id not in self.participants:
            self.participants.append(user.user_id)

    def get_participants(self) -> list[str]:
        return list(self.participants)

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
    ) -> "GroupMeeting":
        return cls(
            str(uuid.uuid4()),
            name,
            location,
            start_time,
            end_time,
            owner_user_id=owner_user_id,
        )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"GroupMeeting({self.name!r}, "
            f"{self.start_time.strftime('%Y-%m-%d %H:%M')}–"
            f"{self.end_time.strftime('%H:%M')}, "
            f"participants={self.participants})"
        )
