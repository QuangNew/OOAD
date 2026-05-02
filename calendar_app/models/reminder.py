from dataclasses import dataclass
import uuid


@dataclass
class Reminder:
    reminder_id: str
    message: str

    @classmethod
    def create(cls, message: str) -> "Reminder":
        return cls(reminder_id=str(uuid.uuid4()), message=message)
