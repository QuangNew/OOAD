from __future__ import annotations
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from models.appointment import Appointment
from models.group_meeting import GroupMeeting
from models.reminder import Reminder
from models.validation_result import ValidationResult
from models.calendar import Calendar
from models.user import User
from storage.file_storage import FileStorage
from workflow_log import workflow_log


class AppointmentController:
    """
    All business rules for the Add Calendar Appointment feature.

    Implements the algorithm described in the Sequence Diagram:
      Step 1 – Validate Input
      Step 2 – Check Time Conflict
      Step 3 – Check Group Meeting Match
      Step 4 – Normal Add

    The controller is the *only* place that calls FileStorage, keeping
    both Calendar (pure in-memory) and CalendarUI (pure view) clean.
    """

    def __init__(self, calendar: Calendar, user: User) -> None:
        workflow_log("Controller", "Initialize appointment controller", f"user_id={user.user_id}")
        self.current_calendar = calendar
        self.current_user = user

    # ------------------------------------------------------------------
    # Primary orchestrator  (Sequence Diagram: handleAddAppointment)
    # ------------------------------------------------------------------

    def handle_add_appointment(
        self,
        name: str,
        location: str,
        start: datetime,
        end: datetime,
        reminder_msg: str,
        reminder_minutes_before: int,
    ) -> ValidationResult:
        """
        Orchestrate the full add-appointment flow.

        Returns a ValidationResult whose fields tell the UI which branch
        to take next:
          • is_valid=False                     → show error message
          • is_valid=True, conflict_appointment → show ConflictDialog
          • is_valid=True, matched_group_meeting → show GroupMeetingDialog
          • is_valid=True (both None)          → appointment was added; refresh
        """
        workflow_log("Controller", "Start add appointment flow", f"duration_min={int((end - start).total_seconds() // 60)}")
        if not self._validate_input(name, start, end):
            msg = self._validation_error_message(name, start, end)
            workflow_log("Controller", "Stop add appointment flow", f"invalid={msg}")
            return ValidationResult(is_valid=False, error_message=msg)

        conflict = self._check_time_conflict(start, end)
        if conflict is not None:
            workflow_log("Controller", "Return conflict branch", f"conflict_id={conflict.appointment_id}")
            return ValidationResult(is_valid=True, conflict_appointment=conflict)

        duration_min = int((end - start).total_seconds() // 60)
        match = self._check_group_meeting_match(name, duration_min)
        if match is not None:
            workflow_log("Controller", "Return group meeting branch", f"meeting_id={match.appointment_id}")
            return ValidationResult(is_valid=True, matched_group_meeting=match)

        appt = self._create_appointment(name, location, start, end, reminder_msg, reminder_minutes_before)
        self.current_calendar.add_appointment(appt)
        FileStorage.save(appt)
        workflow_log("Controller", "Finish normal add branch", f"appointment_id={appt.appointment_id}")
        return ValidationResult(is_valid=True)

    # ------------------------------------------------------------------
    # replaceExistingAppointment  (Sequence Diagram)
    # ------------------------------------------------------------------

    def replace_existing_appointment(
        self,
        old_appt: Appointment,
        name: str,
        location: str,
        start: datetime,
        end: datetime,
        reminder_msg: str,
        reminder_minutes_before: int,
    ) -> None:
        """Remove the conflicting appointment and insert the new one."""
        workflow_log("Controller", "Start replacement flow", f"old_id={old_appt.appointment_id}")
        self.current_calendar.remove_appointment(old_appt)
        FileStorage.delete(old_appt.appointment_id)

        new_appt = self._create_appointment(name, location, start, end, reminder_msg, reminder_minutes_before)
        self.current_calendar.add_appointment(new_appt)
        FileStorage.save(new_appt)
        workflow_log("Controller", "Finish replacement flow", f"new_id={new_appt.appointment_id}")

    # ------------------------------------------------------------------
    # joinExistingGroupMeeting  (Sequence Diagram)
    # ------------------------------------------------------------------

    def join_existing_group_meeting(self, meeting: GroupMeeting) -> None:
        """Add the current user to the group meeting's participant list."""
        workflow_log("Controller", "Start join group meeting flow", f"meeting_id={meeting.appointment_id}")
        meeting.add_participant(self.current_user)
        if all(
            existing.appointment_id != meeting.appointment_id
            for existing in self.current_calendar.get_all()
        ):
            workflow_log("Controller", "Add joined meeting to visible calendar", f"meeting_id={meeting.appointment_id}")
            self.current_calendar.add_appointment(meeting)
        FileStorage.save(meeting)
        workflow_log("Controller", "Finish join group meeting flow", f"participants={len(meeting.participants)}")

    def create_group_meeting(
        self,
        name: str,
        location: str,
        start: datetime,
        end: datetime,
        reminder_msg: str,
        reminder_minutes_before: int,
        participant_ids: list[str] | None = None,
        include_current_user: bool = True,
    ) -> ValidationResult:
        """Create a shared group meeting, optionally joining it immediately."""
        workflow_log("Controller", "Start create group meeting flow", f"include_current_user={include_current_user}")
        if not self._validate_input(name, start, end):
            msg = self._validation_error_message(name, start, end)
            workflow_log("Controller", "Stop create group meeting flow", f"invalid={msg}")
            return ValidationResult(is_valid=False, error_message=msg)

        participant_ids = [item.strip() for item in (participant_ids or []) if item.strip()]
        affects_current_user = (
            include_current_user or self.current_user.user_id in participant_ids
        )

        if affects_current_user:
            workflow_log("Controller", "Check visible-calendar conflict for group meeting")
            conflict = self._check_time_conflict(start, end)
            if conflict is not None:
                workflow_log("Controller", "Return group meeting conflict branch", f"conflict_id={conflict.appointment_id}")
                return ValidationResult(is_valid=True, conflict_appointment=conflict)

        meeting = self._create_group_meeting(
            name,
            location,
            start,
            end,
            reminder_msg,
            reminder_minutes_before,
            participant_ids,
            include_current_user=include_current_user,
        )

        if affects_current_user and all(
            existing.appointment_id != meeting.appointment_id
            for existing in self.current_calendar.get_all()
        ):
            workflow_log("Controller", "Add group meeting to visible calendar", f"meeting_id={meeting.appointment_id}")
            self.current_calendar.add_appointment(meeting)

        FileStorage.save(meeting)
        workflow_log("Controller", "Finish create group meeting flow", f"meeting_id={meeting.appointment_id}")
        return ValidationResult(is_valid=True)

    def update_appointment(
        self,
        existing: Appointment,
        name: str,
        location: str,
        start: datetime,
        end: datetime,
        reminder_msg: str,
        reminder_minutes_before: int,
        participant_ids: list[str] | None = None,
    ) -> ValidationResult:
        """Update an existing appointment while preserving its identity."""
        workflow_log("Controller", "Start update appointment flow", f"appointment_id={existing.appointment_id}")
        if not self._validate_input(name, start, end):
            msg = self._validation_error_message(name, start, end)
            workflow_log("Controller", "Stop update appointment flow", f"invalid={msg}")
            return ValidationResult(is_valid=False, error_message=msg)

        conflict = self._check_time_conflict(
            start,
            end,
            ignore_appointment_id=existing.appointment_id,
        )
        if conflict is not None:
            workflow_log("Controller", "Return update conflict branch", f"conflict_id={conflict.appointment_id}")
            return ValidationResult(is_valid=True, conflict_appointment=conflict)

        if isinstance(existing, GroupMeeting):
            workflow_log("Controller", "Rebuild group meeting")
            updated = self._rebuild_group_meeting(
                existing,
                name,
                location,
                start,
                end,
                reminder_msg,
                reminder_minutes_before,
                participant_ids or [],
            )
        else:
            workflow_log("Controller", "Rebuild personal appointment")
            updated = self._rebuild_appointment(
                existing,
                name,
                location,
                start,
                end,
                reminder_msg,
                reminder_minutes_before,
            )

        self.current_calendar.remove_appointment(existing)
        FileStorage.delete(existing.appointment_id)
        self.current_calendar.add_appointment(updated)
        FileStorage.save(updated)
        workflow_log("Controller", "Finish update appointment flow", f"appointment_id={updated.appointment_id}")
        return ValidationResult(is_valid=True)

    # ------------------------------------------------------------------
    # force_add_appointment
    # Bypasses the group meeting check when the user explicitly chooses
    # NOT to join a matching group meeting and wants their own entry.
    # ------------------------------------------------------------------

    def force_add_appointment(
        self,
        name: str,
        location: str,
        start: datetime,
        end: datetime,
        reminder_msg: str,
        reminder_minutes_before: int,
    ) -> None:
        workflow_log("Controller", "Start force add appointment flow")
        appt = self._create_appointment(name, location, start, end, reminder_msg, reminder_minutes_before)
        self.current_calendar.add_appointment(appt)
        FileStorage.save(appt)
        workflow_log("Controller", "Finish force add appointment flow", f"appointment_id={appt.appointment_id}")

    # ------------------------------------------------------------------
    # delete_appointment  (not in Sequence Diagram but needed by UI)
    # ------------------------------------------------------------------

    def delete_appointment(self, appt: Appointment) -> None:
        workflow_log("Controller", "Start delete appointment flow", f"appointment_id={appt.appointment_id}")
        self.current_calendar.remove_appointment(appt)
        FileStorage.delete(appt.appointment_id)
        workflow_log("Controller", "Finish delete appointment flow", f"appointment_id={appt.appointment_id}")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_input(self, name: str, start: datetime, end: datetime) -> bool:
        return bool(name and name.strip()) and end > start

    def _validation_error_message(
        self, name: str, start: datetime, end: datetime
    ) -> str:
        if not (name and name.strip()):
            return "Appointment name cannot be empty."
        if end <= start:
            return "End time must be after start time."
        return "Invalid input."

    def _check_time_conflict(
        self,
        start: datetime,
        end: datetime,
        ignore_appointment_id: str | None = None,
    ) -> Appointment | None:
        workflow_log(
            "Controller",
            "Check time conflict",
            f"window={start:%Y-%m-%d %H:%M}-{end:%H:%M} ignore_id={ignore_appointment_id or '-'}",
        )
        overlapping = self.current_calendar.get_appointments_by_time(start, end)
        if ignore_appointment_id is not None:
            overlapping = [
                appt for appt in overlapping
                if appt.appointment_id != ignore_appointment_id
            ]
        workflow_log("Controller", "Time conflict result", f"overlap_count={len(overlapping)}")
        return overlapping[0] if overlapping else None

    def _check_group_meeting_match(
        self, name: str, duration: int
    ) -> GroupMeeting | None:
        workflow_log("Controller", "Check group meeting match", f"duration_min={duration}")
        matches = [
            meeting
            for meeting in FileStorage.load_group_meetings(
                exclude_user_id=self.current_user.user_id,
            )
            if meeting.name == name and meeting.duration == duration
        ]
        workflow_log("Controller", "Group meeting match result", f"match_count={len(matches)}")
        return matches[0] if matches else None

    def _create_appointment(
        self,
        name: str,
        location: str,
        start: datetime,
        end: datetime,
        reminder_msg: str,
        reminder_minutes_before: int,
    ) -> Appointment:
        appointment_id = str(uuid.uuid4())
        workflow_log("Controller", "Create appointment object", f"appointment_id={appointment_id}")
        appt = Appointment(
            appointment_id,
            name,
            location,
            start,
            end,
            owner_user_id=self.current_user.user_id,
        )
        self._apply_reminder(appt, reminder_msg, reminder_minutes_before)
        return appt

    def _create_group_meeting(
        self,
        name: str,
        location: str,
        start: datetime,
        end: datetime,
        reminder_msg: str,
        reminder_minutes_before: int,
        participant_ids: list[str],
        include_current_user: bool = True,
    ) -> GroupMeeting:
        workflow_log("Controller", "Create group meeting object", f"participant_inputs={len(participant_ids)}")
        meeting = GroupMeeting.create(
            name,
            location,
            start,
            end,
            owner_user_id=self.current_user.user_id,
        )
        if include_current_user:
            workflow_log("Controller", "Add current user to group meeting", f"user_id={self.current_user.user_id}")
            meeting.add_participant(self.current_user)

        for participant_id in participant_ids:
            clean_id = participant_id.strip()
            if clean_id and clean_id not in meeting.participants:
                meeting.participants.append(clean_id)

        workflow_log("Controller", "Prepared group meeting participants", f"participants={len(meeting.participants)}")
        self._apply_reminder(meeting, reminder_msg, reminder_minutes_before)

        return meeting

    def _rebuild_appointment(
        self,
        existing: Appointment,
        name: str,
        location: str,
        start: datetime,
        end: datetime,
        reminder_msg: str,
        reminder_minutes_before: int,
    ) -> Appointment:
        workflow_log("Controller", "Recreate appointment object", f"appointment_id={existing.appointment_id}")
        appt = Appointment(
            existing.appointment_id,
            name,
            location,
            start,
            end,
            owner_user_id=existing.owner_user_id or self.current_user.user_id,
        )
        self._apply_reminder(appt, reminder_msg, reminder_minutes_before)
        return appt

    def _rebuild_group_meeting(
        self,
        existing: GroupMeeting,
        name: str,
        location: str,
        start: datetime,
        end: datetime,
        reminder_msg: str,
        reminder_minutes_before: int,
        participant_ids: list[str],
    ) -> GroupMeeting:
        workflow_log("Controller", "Recreate group meeting object", f"meeting_id={existing.appointment_id}")
        meeting = GroupMeeting(
            existing.appointment_id,
            name,
            location,
            start,
            end,
            owner_user_id=existing.owner_user_id or self.current_user.user_id,
        )
        meeting.add_participant(self.current_user)

        for participant_id in participant_ids:
            clean_id = participant_id.strip()
            if clean_id and clean_id not in meeting.participants:
                meeting.participants.append(clean_id)

        workflow_log("Controller", "Prepared rebuilt group participants", f"participants={len(meeting.participants)}")
        self._apply_reminder(meeting, reminder_msg, reminder_minutes_before)
        return meeting

    def _apply_reminder(
        self,
        appt: Appointment,
        reminder_msg: str,
        reminder_minutes_before: int,
    ) -> None:
        if reminder_msg and reminder_msg.strip():
            workflow_log("Controller", "Attach reminder", f"minutes_before={reminder_minutes_before}")
            rem = Reminder.create(reminder_msg.strip(), reminder_minutes_before)
            appt.add_reminder(rem)
        else:
            workflow_log("Controller", "Skip reminder", "no message")
