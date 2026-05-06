from dataclasses import dataclass
from datetime import datetime, timedelta
import uuid


@dataclass
class Reminder:
    reminder_id: str
    message: str
    minutes_before: int = 15

    @classmethod
    def create(cls, message: str, minutes_before: int = 15) -> "Reminder":
        return cls(
            reminder_id=str(uuid.uuid4()),
            message=message,
            minutes_before=minutes_before,
        )

    def trigger_time(self, appointment_start: datetime) -> datetime:
        return appointment_start - timedelta(minutes=self.minutes_before)

    @property
    def offset_label(self) -> str:
        if self.minutes_before == 60:
            return "1 hour before"
        return f"{self.minutes_before} minutes before"
