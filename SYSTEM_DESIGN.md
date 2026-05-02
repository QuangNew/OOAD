# SYSTEM_DESIGN.md — Calendar Appointment Application

> **Course:** Object-Oriented Analysis & Design (OOAD)
> **Scope:** Full analysis of Class Diagram & Sequence Diagram + implementation-ready system design

---

## 1. Diagram Analysis

### 1.1 Class Diagram — What Is Good

| Aspect | Assessment |
|--------|------------|
| **MVC-like layering** | `CalendarUI` (View) → `AppointmentController` (Controller) → `Calendar`, `Appointment` (Model). Clean separation. |
| **Composition `User *-- Calendar`** | Correct: a calendar cannot exist without its owner user. 1-to-1 composition is the right choice. |
| **Association `Calendar -- Appointment`** | Correct open association (not composition): appointments can be moved between calendars conceptually; `0..*` multiplicity is accurate. |
| **Aggregation `GroupMeeting o-- User`** | Correct: `GroupMeeting` *holds references* to users but does not own their lifecycle. Open diamond is correct. |
| **Inheritance `GroupMeeting -\|> Appointment`** | Sound design. A group meeting **is-a** appointment with extra participant management. |
| **Derived attribute `/duration`** | Correctly marked with `/` prefix; `calculateDuration()` computes `(endTime - startTime)` in minutes on demand. |
| **`ValidationResult` as a DTO** | Good pattern: avoids returning raw booleans and exceptions together; bundles `isValid`, `errorMessage`, and payload in one object. |
| **`Reminder` aggregated from `Appointment`** | Correct 1-to-many association; reminders don't outlive the appointment in practice. |

---

### 1.2 Class Diagram — Issues & Refinements

#### Issue 1 — `ValidationResult` is missing a `matchedGroupMeeting` field

**Problem:** The sequence diagram shows the controller returning a `ValidationResult` containing a `matchedGroupMeeting` in Step 4 (group meeting match). The current `ValidationResult` only declares `conflictAppointment: Appointment`, which cannot carry a `GroupMeeting` payload in a type-safe way.

**Fix:** Add `matchedGroupMeeting: GroupMeeting` as an optional field.

```
class ValidationResult {
    + isValid : Boolean
    + errorMessage : String
    + conflictAppointment : Appointment      ← for Step 3
    + matchedGroupMeeting : GroupMeeting     ← ADD THIS for Step 4
}
```

---

#### Issue 2 — `Reminder.triggerTime` is never set in the sequence diagram

**Problem:** The sequence shows `C -> Rem : <<create>>(reminderMsg)` — only the message is passed. `triggerTime` is never specified by the user or calculated.

**Fix (two acceptable options):**
- **Option A (simpler):** Remove `triggerTime` from `Reminder`; the reminder fires at `appointment.startTime - N minutes` — derive it at display time only.
- **Option B (explicit):** The form asks the user for a reminder offset (e.g., "15 minutes before"), and `Reminder.__init__(message, offset)` sets `triggerTime = startTime - timedelta(minutes=offset)`.

For a basic app, **Option A** is recommended.

---

#### Issue 3 — `AppointmentController` references `currentCalendar` but not `storage`

**Problem:** The controller needs to persist appointments. As-drawn, `AppointmentController --> Calendar` only shows in-memory manipulation. There is no `Storage` or `Repository` component to handle file I/O.

**Fix:** Add a `FileStorage` (or `CalendarRepository`) dependency to the controller, or document that `Calendar.addAppointment()` / `removeAppointment()` internally trigger `FileStorage` calls.

For this implementation, `Calendar` will delegate persistence to `FileStorage` after every mutation.

---

#### Issue 4 — `CalendarUI` calls `replaceExistingAppointment` and `joinExistingGroupMeeting` directly

**Assessment:** This is acceptable — the UI collects the user's choice from a dialog and then delegates the chosen action to the controller. The `<<uses>>` dependency is correct. No change needed.

---

### 1.3 Sequence Diagram — What Is Good

| Aspect | Assessment |
|--------|------------|
| **`alt/else` fragments** | Correctly model the three decision branches: invalid input, conflict, group meeting match, normal add. |
| **`opt` fragment for Reminder** | Correct optional block; reminder creation is conditional. |
| **`create` lifeline keyword** | Properly shows object instantiation for `Appt` and `Rem`. |
| **`activate/deactivate`** | Correct activation boxes on `UI` and `C` (controller stays active across the whole flow). |
| **Step ordering** | Validation → Conflict check → Group meeting check → Create. The ordering is logically correct: conflict is checked before the more specific group meeting match. |
| **Self-call `C -> C`** | `validateInput` and `checkTimeConflict` are internal to the controller; self-calls are appropriate. |

---

### 1.4 Sequence Diagram — Issues & Refinements

#### Issue 1 — Inconsistent naming of the new appointment object

**Problem:** In the conflict branch, `create Appt` creates a lifeline named `Appt`, but `addAppointment(newAppt)` uses a different variable name `newAppt`. This implies two different objects.

**Fix:** Keep the created lifeline as `appt : Appointment` and pass the same reference: `Cal.addAppointment(appt)`.

---

#### Issue 2 — `getAppointmentsByTime` is called before `checkTimeConflict`

**Assessment:** These two look redundant — `getAppointmentsByTime` fetches the list, then `checkTimeConflict` searches that list. In implementation, combine them: `checkTimeConflict` internally calls `Calendar.getAppointmentsByTime()` and evaluates overlap. The sequence diagram shows it as two steps for educational clarity, which is fine.

---

#### Issue 3 — `replaceExistingAppointment` is called from `UI` not from `C`

**Problem:** After the user confirms "Replace", the sequence shows `UI -> C : replaceExistingAppointment(oldAppt, newAppt)`. This means `UI` knows about both the old and new appointment objects — it received `oldAppt` from `ValidationResult` and the new details from the form. This is a reasonable design, but the `UI` is holding domain data.

**Assessment:** Acceptable for this scope. A stricter design would have `UI` tell the `C` to "proceed with replacement using the same form data" and let `C` construct the new appointment. Both are valid in OOAD context.

---

## 2. Final Class Design

### 2.1 Class Responsibilities

```
┌──────────────────────────────────────────────────────────────────────┐
│  CalendarUI                                                          │
│  ─────────                                                           │
│  Owns the tkinter main window, calendar grid, and appointment list.  │
│  Opens dialog windows and relays user decisions to the controller.   │
│  Never performs business logic — only calls controller methods.      │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  AppointmentController                                               │
│  ─────────────────────                                               │
│  Single class responsible for ALL business rules:                    │
│   • input validation                                                 │
│   • conflict detection                                               │
│   • group meeting matching                                           │
│   • orchestrating Calendar mutations                                 │
│  Returns ValidationResult objects to the UI; never touches widgets. │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  Calendar                                                            │
│  ────────                                                            │
│  In-memory container of all appointments for one user.               │
│  Provides query methods (by time range, by name+duration).           │
│  On every mutation (add/remove), delegates to FileStorage.           │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  Appointment                                                         │
│  ───────────                                                         │
│  Pure data object. duration is a derived @property in Python.        │
│  addReminder() appends to its internal reminders list.               │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  GroupMeeting  (extends Appointment)                                 │
│  ─────────────                                                       │
│  Adds participants: List[User]. All appointment fields inherited.    │
│  addParticipant() appends and persists via Calendar/Storage.         │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  ValidationResult  (DTO)                                             │
│  ─────────────────                                                   │
│  Carries the outcome of any controller check back to the UI.         │
│  Fields:                                                             │
│    isValid: bool                                                     │
│    errorMessage: str                                                 │
│    conflictAppointment: Appointment | None                           │
│    matchedGroupMeeting: GroupMeeting | None  ← refined               │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  FileStorage                                                         │
│  ───────────                                                         │
│  Static helper (not in original diagram — added for implementation). │
│  Handles all JSON-in-TXT read/write.                                 │
│  load_all() → List[Appointment | GroupMeeting]                       │
│  save(appt) → writes file                                            │
│  delete(appt_id) → removes file                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

### 2.2 Relationships Summary

| Relationship | Type | UML Notation | Reason |
|-------------|------|-------------|--------|
| `CalendarUI` → `AppointmentController` | Dependency (uses) | `..>` | UI calls controller methods; no long-lived reference needed |
| `AppointmentController` → `Calendar` | Association | `-->` | Controller holds a reference to the calendar for the session |
| `AppointmentController` → `Appointment` | Dependency (creates) | `..>` | Controller instantiates appointments on demand |
| `AppointmentController` → `ValidationResult` | Dependency (creates) | `..>` | Controller constructs and returns result objects |
| `User` *──* `Calendar` | Composition | `*--` | Calendar's existence depends on its owner user |
| `Calendar` ── `Appointment` | Association | `--` | Calendar records appointments; appointments can be queried |
| `Appointment` ── `Reminder` | Association | `--` | Each appointment may have zero or more reminders |
| `GroupMeeting` ──▷ `Appointment` | Inheritance | `-\|>` | GroupMeeting IS-A Appointment with extra participant data |
| `GroupMeeting` ◇── `User` | Aggregation | `o--` | GroupMeeting references users; does not own their lifecycle |

---

## 3. Algorithm: Add Calendar Appointment

The following is the authoritative step-by-step algorithm matching the Sequence Diagram.

```
handleAddAppointment(name, location, start, end, reminderMsg):

  STEP 1 — Validate Input
  ─────────────────────────
  IF name is empty OR start >= end:
      RETURN ValidationResult(isValid=False, errorMessage="Invalid input")
      → UI shows error message
      → STOP

  STEP 2 — Check Time Conflict
  ─────────────────────────────
  candidates = calendar.getAppointmentsByTime(start, end)
        └─ returns all appointments where: appt.start < end AND appt.end > start

  conflict = first item in candidates (if any)

  IF conflict exists:
      RETURN ValidationResult(isValid=True, conflictAppointment=conflict)
      → UI shows ConflictDialog with the conflicting appointment

      IF user chooses "Replace":
          GOTO replaceExistingAppointment(conflict, newApptData)
      ELSE:
          STOP (user cancels or picks a different time)

  STEP 3 — Check Group Meeting Match
  ────────────────────────────────────
  duration = (end - start) in minutes
  candidates = calendar.getGroupMeetingsByNameAndDuration(name, duration)
        └─ returns GroupMeetings where: gm.name == name AND gm.duration == duration

  match = first item in candidates (if any)

  IF match exists:
      RETURN ValidationResult(isValid=True, matchedGroupMeeting=match)
      → UI shows GroupMeetingDialog

      IF user chooses "Join":
          GOTO joinExistingGroupMeeting(match, currentUser)
      ELSE:
          GOTO normalAdd (user wants a separate appointment)

  STEP 4 — Normal Add
  ─────────────────────
  appt = new Appointment(name, location, start, end)
  IF reminderMsg is not empty:
      rem = new Reminder(message=reminderMsg)
      appt.addReminder(rem)
  calendar.addAppointment(appt)   ← persists to file
  RETURN Success


replaceExistingAppointment(old, newData):
  calendar.removeAppointment(old)   ← deletes old file
  appt = new Appointment(newData)
  IF reminderMsg is not empty:
      rem = new Reminder(message=reminderMsg)
      appt.addReminder(rem)
  calendar.addAppointment(appt)     ← writes new file
  RETURN Success


joinExistingGroupMeeting(meeting, user):
  meeting.addParticipant(user)      ← updates participants list
  fileStorage.save(meeting)         ← overwrites existing gm file
  RETURN Success
```

---

## 4. Module Breakdown

### 4.1 `models/validation_result.py`

```python
@dataclass
class ValidationResult:
    is_valid: bool
    error_message: str = ""
    conflict_appointment: "Appointment | None" = None
    matched_group_meeting: "GroupMeeting | None" = None
```

### 4.2 `models/reminder.py`

```python
@dataclass
class Reminder:
    reminder_id: str          # uuid
    message: str
    # triggerTime omitted (basic app) or derived as startTime - offset
```

### 4.3 `models/appointment.py`

```python
class Appointment:
    def __init__(self, appointment_id, name, location, start_time, end_time):
        self.appointment_id = appointment_id
        self.name = name
        self.location = location
        self.start_time = start_time    # datetime
        self.end_time = end_time        # datetime
        self.reminders: list[Reminder] = []

    @property
    def duration(self) -> int:
        """Derived: minutes between start and end."""
        return int((self.end_time - self.start_time).total_seconds() // 60)

    def add_reminder(self, rem: Reminder) -> None:
        self.reminders.append(rem)
```

### 4.4 `models/group_meeting.py`

```python
class GroupMeeting(Appointment):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.participants: list[str] = []   # list of userId strings

    def add_participant(self, user: User) -> None:
        if user.user_id not in self.participants:
            self.participants.append(user.user_id)

    def get_participants(self) -> list[str]:
        return self.participants
```

### 4.5 `models/calendar.py`

```python
class Calendar:
    def __init__(self, calendar_id: str):
        self.calendar_id = calendar_id
        self._appointments: list[Appointment] = []

    def add_appointment(self, appt: Appointment) -> None:
        self._appointments.append(appt)
        FileStorage.save(appt)

    def remove_appointment(self, appt: Appointment) -> None:
        self._appointments = [a for a in self._appointments
                               if a.appointment_id != appt.appointment_id]
        FileStorage.delete(appt.appointment_id)

    def get_appointments_by_time(self, start, end) -> list[Appointment]:
        """Returns all appointments that overlap [start, end)."""
        return [a for a in self._appointments
                if a.start_time < end and a.end_time > start]

    def get_group_meetings_by_name_and_duration(self, name: str, duration: int):
        return [a for a in self._appointments
                if isinstance(a, GroupMeeting)
                and a.name == name
                and a.duration == duration]
```

### 4.6 `controller/appointment_controller.py`

```python
class AppointmentController:
    def __init__(self, calendar: Calendar, user: User):
        self.current_calendar = calendar
        self.current_user = user

    def handle_add_appointment(self, name, location, start, end, reminder_msg) -> ValidationResult:
        # Step 1: Validate
        if not self._validate_input(name, start, end):
            return ValidationResult(is_valid=False, error_message="Invalid input")

        # Step 2: Conflict check
        conflict = self._check_time_conflict(start, end)
        if conflict:
            return ValidationResult(is_valid=True, conflict_appointment=conflict)

        # Step 3: Group meeting match
        duration = int((end - start).total_seconds() // 60)
        match = self._check_group_meeting_match(name, duration)
        if match:
            return ValidationResult(is_valid=True, matched_group_meeting=match)

        # Step 4: Normal add
        appt = self._create_appointment(name, location, start, end, reminder_msg)
        self.current_calendar.add_appointment(appt)
        return ValidationResult(is_valid=True)

    def replace_existing_appointment(self, old_appt, name, location, start, end, reminder_msg):
        self.current_calendar.remove_appointment(old_appt)
        appt = self._create_appointment(name, location, start, end, reminder_msg)
        self.current_calendar.add_appointment(appt)

    def join_existing_group_meeting(self, meeting: GroupMeeting):
        meeting.add_participant(self.current_user)
        FileStorage.save(meeting)

    # ── private helpers ─────────────────────────────────────────────

    def _validate_input(self, name, start, end) -> bool:
        return bool(name and name.strip()) and end > start

    def _check_time_conflict(self, start, end) -> "Appointment | None":
        overlaps = self.current_calendar.get_appointments_by_time(start, end)
        return overlaps[0] if overlaps else None

    def _check_group_meeting_match(self, name, duration) -> "GroupMeeting | None":
        matches = self.current_calendar.get_group_meetings_by_name_and_duration(name, duration)
        return matches[0] if matches else None

    def _create_appointment(self, name, location, start, end, reminder_msg) -> Appointment:
        appt = Appointment(str(uuid.uuid4()), name, location, start, end)
        if reminder_msg and reminder_msg.strip():
            rem = Reminder(str(uuid.uuid4()), reminder_msg)
            appt.add_reminder(rem)
        return appt
```

---

## 5. Storage Design

### Folder Structure at Runtime

```
data/
├── user.txt
├── appointments/
│   ├── appt_550e8400-e29b-41d4-a716-446655440000.txt
│   └── appt_6ba7b810-9dad-11d1-80b4-00c04fd430c8.txt
└── group_meetings/
    └── gm_6ba7b811-9dad-11d1-80b4-00c04fd430c8.txt
```

### `FileStorage` Contract

| Method | Purpose |
|--------|---------|
| `load_all() -> list[Appointment]` | Read all files from both subfolders; deserialize to objects |
| `save(appt: Appointment) -> None` | Serialize to JSON; write to correct subfolder |
| `delete(appt_id: str) -> None` | Find and remove the file with matching UUID name |

### Serialization Rules

| Python field | JSON key | Notes |
|-------------|---------|-------|
| `appointment_id` | `"appointmentId"` | UUID string |
| `start_time` | `"startTime"` | ISO 8601 string |
| `end_time` | `"endTime"` | ISO 8601 string |
| `reminders` | `"reminders"` | Array of reminder objects |
| `participants` | `"participants"` | Array of userId strings (GroupMeeting only) |
| `is_group_meeting` | `"isGroupMeeting"` | `true` / `false` — routing flag |

---

## 6. Data Flow Diagram

```
User Input (tkinter form)
        │
        ▼
   CalendarUI.submitAppointmentForm()
        │
        ▼ calls
   AppointmentController.handleAddAppointment(...)
        │
        ├─── validateInput()                ──► ValidationResult(invalid) ──► UI shows error
        │
        ├─── Calendar.getAppointmentsByTime()
        │    └─── checkTimeConflict()       ──► ValidationResult(conflict) ──► UI: ConflictDialog
        │              │ user says Replace
        │              ▼
        │    replaceExistingAppointment()
        │         ├── Calendar.removeAppointment() → FileStorage.delete()
        │         └── Calendar.addAppointment()    → FileStorage.save()
        │
        ├─── Calendar.getGroupMeetingsByNameAndDuration()
        │    └─── checkGroupMeetingMatch()  ──► ValidationResult(match) ──► UI: GroupMeetingDialog
        │              │ user says Join
        │              ▼
        │    joinExistingGroupMeeting() → FileStorage.save() (update participants)
        │
        └─── Normal path:
             new Appointment() [+ new Reminder()]
             Calendar.addAppointment() → FileStorage.save()

        ▼
   UI: close dialog, refresh calendar grid
```

---

## 7. Overlap Detection — Mathematical Definition

Two appointments A and B **overlap** if and only if:

$$A_{start} < B_{end} \quad \text{AND} \quad A_{end} > B_{start}$$

This is the standard interval-overlap test. In Python:

```python
def overlaps(a: Appointment, start: datetime, end: datetime) -> bool:
    return a.start_time < end and a.end_time > start
```

Edge cases:
- Back-to-back appointments (A ends exactly when B starts) do **not** overlap: `A.end == B.start` → `A.end > B.start` is `False`.
- Appointments that are completely inside another one are caught correctly.

---

## 8. Design Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Persistence layer | `FileStorage` helper class outside the UML diagram | Keeps `Calendar` clean; separates I/O from domain logic |
| `ValidationResult` | Add `matchedGroupMeeting` field | Avoids unsafe cast from `Appointment` to `GroupMeeting` |
| `Reminder.triggerTime` | Omit for basic version | Form never asks for it; derive from `startTime` if needed |
| GroupMeeting match | Exact name + exact duration in minutes | Mirrors the diagram spec; simple equality check |
| Conflict = first overlap only | Return the first found | Avoids presenting multiple dialogs in sequence; sufficient for basic app |
| Python `@property` for `duration` | Yes | Cleanly models the `/duration` derived attribute from the class diagram |
| Inheritance over composition for `GroupMeeting` | Inheritance | Exactly matches the UML `extends` relationship and simplifies serialization |
