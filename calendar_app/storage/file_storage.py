from __future__ import annotations
import hashlib
import json
import uuid
from datetime import date, datetime, time, timedelta
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
_ACCOUNTS_FILE = _DATA_DIR / "accounts.txt"


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
    # Account authentication
    # ------------------------------------------------------------------

    @classmethod
    def load_accounts(cls) -> list[dict]:
        if not _ACCOUNTS_FILE.exists():
            return []
        try:
            with _ACCOUNTS_FILE.open(encoding="utf-8") as f:
                payload = json.load(f)
        except (json.JSONDecodeError, OSError):
            cls._warn(f"Could not read accounts file: {_ACCOUNTS_FILE}")
            return []

        if isinstance(payload, dict):
            accounts = payload.get("accounts", [])
            return accounts if isinstance(accounts, list) else []
        if isinstance(payload, list):
            return payload
        return []

    @classmethod
    def _save_accounts(cls, accounts: list[dict]) -> None:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        with _ACCOUNTS_FILE.open("w", encoding="utf-8") as f:
            json.dump({"accounts": accounts}, f, indent=2, ensure_ascii=False)

    @classmethod
    def authenticate_user(cls, username: str, password: str) -> User | None:
        normalized = cls._normalize_username(username)
        password_hash = cls._hash_password(password)

        for account in cls.load_accounts():
            if account.get("username") != normalized:
                continue
            if account.get("passwordHash") != password_hash:
                return None
            return cls._user_from_account(account)
        return None

    @classmethod
    def register_user(cls, full_name: str, username: str, password: str) -> User:
        clean_name = full_name.strip()
        clean_username = cls._normalize_username(username)

        if len(clean_name) < 2:
            raise ValueError("Full name must be at least 2 characters.")
        if len(clean_username) < 3:
            raise ValueError("Username must be at least 3 characters.")
        if not cls._is_valid_username(clean_username):
            raise ValueError("Username can contain only letters, numbers, dot, underscore, and dash.")
        if len(password) < 4:
            raise ValueError("Password must be at least 4 characters.")

        accounts = cls.load_accounts()
        if any(account.get("username") == clean_username for account in accounts):
            raise ValueError("Username already exists.")

        account = {
            "userId": str(uuid.uuid4()),
            "fullName": clean_name,
            "username": clean_username,
            "passwordHash": cls._hash_password(password),
        }
        accounts.append(account)
        cls._save_accounts(accounts)
        return cls._user_from_account(account)

    @classmethod
    def _user_from_account(cls, account: dict) -> User:
        return User(
            user_id=account["userId"],
            full_name=account["fullName"],
            username=account.get("username", ""),
        )

    @staticmethod
    def _normalize_username(username: str) -> str:
        return username.strip().lower()

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    @staticmethod
    def _is_valid_username(username: str) -> bool:
        allowed = {".", "_", "-"}
        return bool(username) and all(char.isalnum() or char in allowed for char in username)

    # ------------------------------------------------------------------
    # Demo data
    # ------------------------------------------------------------------

    @classmethod
    def seed_demo_meetings_for_user(cls, user: User) -> None:
        slots = [
            (1, time(9, 0), 60, "Sprint Planning", "Main Meeting Room", ["pm.linh", "dev.huy"]),
            (2, time(14, 0), 90, "Product Review", "Zoom", ["design.mai", "qa.an"]),
            (4, time(16, 0), 45, "Weekly Retrospective", "Innovation Hub", ["lead.nam", "ops.trang"]),
        ]

        for days_ahead, start_at, duration_min, name, location, participants in slots:
            start = datetime.combine(date.today() + timedelta(days=days_ahead), start_at)
            meeting = GroupMeeting.create(
                name,
                location,
                start,
                start + timedelta(minutes=duration_min),
                owner_user_id=user.user_id,
            )
            meeting.add_participant(user)
            for participant in participants:
                if participant not in meeting.participants:
                    meeting.participants.append(participant)
            cls.save(meeting)

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
                if appt is not None and appt.owner_user_id == user_id:
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
            "ownerUserId": appt.owner_user_id,
            "reminders": [
                {
                    "reminderId": r.reminder_id,
                    "message": r.message,
                    "minutesBefore": r.minutes_before,
                }
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
        owner_user_id = data.get("ownerUserId")

        if data.get("isGroupMeeting"):
            appt: Appointment = GroupMeeting(
                data["appointmentId"], data["name"],
                data["location"], start, end,
                owner_user_id=owner_user_id,
            )
            appt.participants = data.get("participants", [])  # type: ignore[attr-defined]
        else:
            appt = Appointment(
                data["appointmentId"], data["name"],
                data["location"], start, end,
                owner_user_id=owner_user_id,
            )

        for r in data.get("reminders", []):
            appt.reminders.append(
                Reminder(
                    r["reminderId"],
                    r["message"],
                    int(r.get("minutesBefore", 15)),
                )
            )

        return appt
