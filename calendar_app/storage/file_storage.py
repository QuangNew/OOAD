from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path

from models.appointment import Appointment
from models.group_meeting import GroupMeeting
from models.reminder import Reminder
from models.user import User

# ---------------------------------------------------------------------------
# Path layout
#   calendar_app/
#     storage/file_storage.py   ← __file__
#     data/
#       user.txt
#       appointments/appt_<uuid>.txt
#       group_meetings/gm_<uuid>.txt
# ---------------------------------------------------------------------------
_DATA_DIR  = Path(__file__).resolve().parent.parent / "data"
_APPT_DIR  = _DATA_DIR / "appointments"
_GM_DIR    = _DATA_DIR / "group_meetings"
_USER_FILE = _DATA_DIR / "user.txt"


class FileStorage:
    """Static helper: all JSON-in-TXT read / write operations."""

    _load_warnings: list[str] = []

    # ------------------------------------------------------------------
    # Directory bootstrap
    # ------------------------------------------------------------------

    @classmethod
    def _ensure_dirs(cls) -> None:
        _APPT_DIR.mkdir(parents=True, exist_ok=True)
        _GM_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _warn(cls, message: str) -> None:
        cls._load_warnings.append(message)

    @classmethod
    def consume_warnings(cls) -> list[str]:
        warnings = list(cls._load_warnings)
        cls._load_warnings.clear()
        return warnings

    # ------------------------------------------------------------------
    # User
    # ------------------------------------------------------------------

    @classmethod
    def load_user(cls) -> dict | None:
        if not _USER_FILE.exists():
            return None
        try:
            with _USER_FILE.open(encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            cls._warn(f"Could not read user profile: {_USER_FILE}")
            return None

    @classmethod
    def save_user(cls, user: User) -> None:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        with _USER_FILE.open("w", encoding="utf-8") as f:
            json.dump({"userId": user.user_id, "fullName": user.full_name}, f, indent=2)

    # ------------------------------------------------------------------
    # Appointments
    # ------------------------------------------------------------------

    @classmethod
    def save(cls, appt: Appointment) -> None:
        cls._ensure_dirs()
        data = cls._serialize(appt)
        folder = _GM_DIR if appt.is_group_meeting else _APPT_DIR
        prefix = "gm" if appt.is_group_meeting else "appt"
        path = folder / f"{prefix}_{appt.appointment_id}.txt"
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def delete(cls, appointment_id: str) -> None:
        for folder in (_APPT_DIR, _GM_DIR):
            for fpath in folder.glob(f"*_{appointment_id}.txt"):
                try:
                    fpath.unlink()
                except OSError:
                    pass
                return  # one file per ID

    @classmethod
    def load_all(cls) -> list[Appointment]:
        cls._ensure_dirs()
        results: list[Appointment] = []
        for folder in (_APPT_DIR, _GM_DIR):
            for fpath in sorted(folder.glob("*.txt")):
                try:
                    with fpath.open(encoding="utf-8") as f:
                        data = json.load(f)
                    appt = cls._deserialize(data)
                    if appt is not None:
                        results.append(appt)
                except (json.JSONDecodeError, KeyError, ValueError):
                    cls._warn(f"Skipped unreadable appointment file: {fpath}")
        return results

    @classmethod
    def load_calendar_items_for_user(cls, user_id: str) -> list[Appointment]:
        """
        Load the current user's visible calendar items.

        Personal appointments are always included. Group meetings are included
        only when the user is a participant, which keeps the shared meeting
        directory separate from the user's own calendar schedule.
        """
        items: list[Appointment] = []
        cls._ensure_dirs()

        for fpath in sorted(_APPT_DIR.glob("*.txt")):
            try:
                with fpath.open(encoding="utf-8") as f:
                    data = json.load(f)
                appt = cls._deserialize(data)
                if appt is not None:
                    items.append(appt)
            except (json.JSONDecodeError, KeyError, ValueError):
                cls._warn(f"Skipped unreadable appointment file: {fpath}")

        for meeting in cls.load_group_meetings(include_user_id=user_id):
            items.append(meeting)

        return items

    @classmethod
    def load_group_meetings(
        cls,
        include_user_id: str | None = None,
        exclude_user_id: str | None = None,
    ) -> list[GroupMeeting]:
        """
        Load shared group meetings from the dedicated storage directory.

        Filters:
          * include_user_id – keep only meetings that include this user
          * exclude_user_id – drop meetings that include this user
        """
        cls._ensure_dirs()
        meetings: list[GroupMeeting] = []

        for fpath in sorted(_GM_DIR.glob("*.txt")):
            try:
                with fpath.open(encoding="utf-8") as f:
                    data = json.load(f)
                appt = cls._deserialize(data)
                if not isinstance(appt, GroupMeeting):
                    continue
                if include_user_id is not None and include_user_id not in appt.participants:
                    continue
                if exclude_user_id is not None and exclude_user_id in appt.participants:
                    continue
                meetings.append(appt)
            except (json.JSONDecodeError, KeyError, ValueError):
                cls._warn(f"Skipped unreadable group meeting file: {fpath}")

        return meetings

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    @classmethod
    def _serialize(cls, appt: Appointment) -> dict:
        data: dict = {
            "appointmentId": appt.appointment_id,
            "name": appt.name,
            "location": appt.location,
            "startTime": appt.start_time.isoformat(),
            "endTime":   appt.end_time.isoformat(),
            "isGroupMeeting": appt.is_group_meeting,
            "reminders": [
                {"reminderId": r.reminder_id, "message": r.message}
                for r in appt.reminders
            ],
        }
        if isinstance(appt, GroupMeeting):
            data["participants"] = appt.participants
        return data

    @classmethod
    def _deserialize(cls, data: dict) -> Appointment | None:
        start = datetime.fromisoformat(data["startTime"])
        end   = datetime.fromisoformat(data["endTime"])

        if data.get("isGroupMeeting"):
            appt: Appointment = GroupMeeting(
                data["appointmentId"], data["name"],
                data["location"], start, end,
            )
            appt.participants = data.get("participants", [])  # type: ignore[attr-defined]
        else:
            appt = Appointment(
                data["appointmentId"], data["name"],
                data["location"], start, end,
            )

        for r in data.get("reminders", []):
            appt.reminders.append(Reminder(r["reminderId"], r["message"]))

        return appt
