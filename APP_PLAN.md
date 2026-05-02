# APP_PLAN.md — Calendar Appointment Application

> **Course:** Object-Oriented Analysis & Design (OOAD)
> **Feature:** Add Calendar Appointment
> **Stack:** Python · Tkinter · Local TXT/JSON files (no database)

---

## 1. Project Overview

A desktop calendar application that lets a single user manage personal appointments. The primary feature under development is **Add Calendar Appointment**, following the algorithm defined in the Sequence Diagram. The app stores all data locally in structured text files — no database, no external service.

---

## 2. Functional Scope

### Core Features (must-have)
| # | Feature | Description |
|---|---------|-------------|
| 1 | View Calendar | Monthly grid showing dates; click a date to see its appointments |
| 2 | Add Appointment | Form dialog: name, location, start/end time, optional reminder |
| 3 | Input Validation | Block empty name, negative/zero duration, malformed time |
| 4 | Time Conflict Check | Detect overlap with existing appointments |
| 5 | Replace on Conflict | User can choose to overwrite the conflicting appointment |
| 6 | Group Meeting Match | Detect existing meetings with same name + duration; prompt to join |
| 7 | Add Reminder | Optional reminder message attached to an appointment |
| 8 | Delete Appointment | Remove an appointment from the list |
| 9 | Appointment Detail | Click an appointment to see full info |

### Out of Scope (keep it basic)
- Multi-user login / authentication
- Network sync or cloud backup
- Recurring appointments
- Drag-and-drop rescheduling
- Notifications / pop-up reminders at runtime

---

## 3. Technology Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| Language | Python 3.11+ | Requirement |
| GUI | `tkinter` + `ttk` | Built-in, no install needed |
| Data storage | Plain `.txt` files (JSON-formatted) | Requirement — no database |
| Date/time | `datetime` (stdlib) | No extra dependency |
| Unique IDs | `uuid` (stdlib) | Stable, collision-free file names |

---

## 4. UI / UX Design

Inspired by **Cal.com** (clean neutral, developer-oriented simplicity — from `awesome-design-md`).

### Color Palette

| Role | Token | Hex |
|------|-------|-----|
| Primary / Ink | `ink` | `#111111` |
| Canvas (bg) | `canvas` | `#FFFFFF` |
| Soft surface | `surface-soft` | `#F8F9FA` |
| Card | `surface-card` | `#F5F5F5` |
| Border / Hairline | `hairline` | `#E5E7EB` |
| Accent (links, active) | `brand-accent` | `#3B82F6` |
| Body text | `body` | `#374151` |
| Muted text | `muted` | `#6B7280` |
| Danger / error | `danger` | `#EF4444` |
| Success | `success` | `#22C55E` |

### Typography (Tkinter fonts)
| Style | Font | Size | Weight |
|-------|------|------|--------|
| Window title | Segoe UI | 14 | bold |
| Section heading | Segoe UI | 11 | bold |
| Body / labels | Segoe UI | 10 | normal |
| Small / muted | Segoe UI | 9 | normal |
| Calendar day number | Segoe UI | 10 | bold |

### Main Window Layout (ASCII wireframe)
```
┌─────────────────────────────────────────────────────────────────┐
│  📅  Calendar App                              [User: Guest]     │
├────────────────────────────────┬────────────────────────────────┤
│  ◀  May 2026  ▶                │  Appointments on May 2, 2026   │
│  ─────────────────────────── │  ──────────────────────────────  │
│  Mo  Tu  We  Th  Fr  Sa  Su  │  ┌──────────────────────────┐   │
│                  1   2   3   │  │ 09:00–10:00  Team Meeting  │   │
│   4   5   6   7   8   9  10  │  │ Location: Room 301         │   │
│  11  12  13  14  15  16  17  │  │ ⏰ Standup reminder        │   │
│  18  19  20  21  22  23  24  │  └──────────────────────────┘   │
│  25  26  27  28  29  30  31  │  ┌──────────────────────────┐   │
│                              │  │ 14:00–15:00  Doctor Visit  │   │
│  [+ Add Appointment]         │  └──────────────────────────┘   │
│                              │                                   │
│                              │  [🗑 Delete Selected]            │
└────────────────────────────────┴────────────────────────────────┘
```

### Add Appointment Dialog (ASCII wireframe)
```
┌────────────────────────────────────────┐
│  Add New Appointment               [✕] │
├────────────────────────────────────────┤
│  Name *        [________________________]│
│  Location      [________________________]│
│  Start Date *  [YYYY-MM-DD]             │
│  Start Time *  [HH:MM]                  │
│  End Date *    [YYYY-MM-DD]             │
│  End Time *    [HH:MM]                  │
│                                        │
│  ☐ Add Reminder                        │
│    Message  [________________________] │
│                                        │
│  ────────────────────────────────────  │
│         [Cancel]          [Add →]      │
└────────────────────────────────────────┘
```

### Conflict Warning Dialog
```
┌────────────────────────────────────────┐
│  ⚠ Time Conflict Detected         [✕] │
├────────────────────────────────────────┤
│  This time slot overlaps with:         │
│                                        │
│    "Team Meeting"                      │
│    09:00 – 10:00                       │
│                                        │
│  Do you want to replace it?            │
│                                        │
│         [Keep Old]    [Replace →]      │
└────────────────────────────────────────┘
```

### Group Meeting Prompt Dialog
```
┌────────────────────────────────────────┐
│  📢 Group Meeting Found            [✕] │
├────────────────────────────────────────┤
│  A group meeting with the same name    │
│  and duration already exists:          │
│                                        │
│    "Team Meeting"  (60 min)            │
│    Participants: Alice, Bob            │
│                                        │
│  Join this meeting?                    │
│                                        │
│         [No, New Appt]   [Join →]      │
└────────────────────────────────────────┘
```

---

## 5. Project File Structure

```
calendar_app/
│
├── main.py                          # Entry point — bootstraps User, Calendar, launches UI
│
├── ui/
│   ├── __init__.py
│   ├── calendar_ui.py               # CalendarUI class — main window, calendar grid
│   ├── appointment_dialog.py        # Add Appointment form dialog
│   ├── conflict_dialog.py           # Time conflict warning dialog
│   ├── group_meeting_dialog.py      # Join group meeting prompt dialog
│   └── appointment_detail.py        # Appointment detail view panel
│
├── controller/
│   ├── __init__.py
│   └── appointment_controller.py    # AppointmentController — all business logic
│
├── models/
│   ├── __init__.py
│   ├── user.py                      # User
│   ├── calendar.py                  # Calendar (owns List[Appointment])
│   ├── appointment.py               # Appointment + derived duration property
│   ├── group_meeting.py             # GroupMeeting (extends Appointment)
│   ├── reminder.py                  # Reminder
│   └── validation_result.py         # ValidationResult (DTO)
│
├── storage/
│   ├── __init__.py
│   └── file_storage.py              # Read/write .txt files; serialize/deserialize
│
└── data/                            # Runtime-generated data folder (gitignored)
    ├── user.txt                     # Single user profile
    ├── appointments/                # One file per appointment
    │   └── appt_<uuid>.txt
    └── group_meetings/              # One file per group meeting
        └── gm_<uuid>.txt
```

---

## 6. Data Storage Design

All files use **JSON format** stored with a `.txt` extension to satisfy the "txt files" requirement while keeping parsing simple and robust.

### `data/user.txt`
```json
{
  "userId": "user-001",
  "fullName": "Guest User"
}
```

### `data/appointments/appt_<uuid>.txt`
```json
{
  "appointmentId": "a1b2c3d4-...",
  "name": "Team Meeting",
  "location": "Room 301",
  "startTime": "2026-05-02T09:00:00",
  "endTime": "2026-05-02T10:00:00",
  "isGroupMeeting": false,
  "reminders": [
    {
      "reminderId": "r1a2b3-...",
      "triggerTime": "2026-05-02T08:45:00",
      "message": "Standup in 15 minutes"
    }
  ]
}
```

### `data/group_meetings/gm_<uuid>.txt`
```json
{
  "appointmentId": "g9h8i7j6-...",
  "name": "Team Meeting",
  "location": "Room 301",
  "startTime": "2026-05-02T09:00:00",
  "endTime": "2026-05-02T10:00:00",
  "isGroupMeeting": true,
  "participants": ["user-001", "user-002"],
  "reminders": []
}
```

**Design decisions:**
- `GroupMeeting` is a superset of `Appointment`; the extra `participants` field distinguishes it
- `isGroupMeeting: bool` flag lets the storage layer route files to the correct subfolder
- All times stored in **ISO 8601** (`YYYY-MM-DDTHH:MM:SS`) for unambiguous parsing
- UUIDs as file names ensure no collisions and easy lookup

---

## 7. Implementation Phases

### Phase 1 — Core Models & Storage (no GUI)
- [ ] `models/` — implement all five model classes
- [ ] `storage/file_storage.py` — `save_appointment`, `load_all_appointments`, `delete_appointment`
- [ ] Manual test: create, save, load, delete an appointment via Python REPL

### Phase 2 — Controller Logic
- [ ] `AppointmentController.validateInput()`
- [ ] `AppointmentController.checkTimeConflict()`
- [ ] `AppointmentController.checkGroupMeetingMatch()`
- [ ] `AppointmentController.handleAddAppointment()` — full orchestration
- [ ] `AppointmentController.replaceExistingAppointment()`
- [ ] `AppointmentController.joinExistingGroupMeeting()`
- [ ] Unit test each method with edge cases

### Phase 3 — Main Window GUI
- [ ] `CalendarUI` — main window, monthly grid
- [ ] Date cell click → show appointments in right panel
- [ ] "Add Appointment" button → open `AppointmentDialog`

### Phase 4 — Dialogs
- [ ] `AppointmentDialog` — form + submit → calls controller
- [ ] `ConflictDialog` — shows conflict, returns user choice
- [ ] `GroupMeetingDialog` — shows match, returns user choice

### Phase 5 — Integration & Polish
- [ ] Wire all dialogs into the controller flow
- [ ] Appointment detail view (click to expand)
- [ ] Delete appointment button
- [ ] Error handling for corrupted/missing data files
- [ ] Smoke-test the full Add Appointment flow end-to-end

---

## 8. Key Constraints & Decisions

| Constraint | Decision |
|-----------|----------|
| No database | JSON-in-TXT files; one file per appointment |
| Single user | Hard-code one user profile; no login screen |
| Basic UI | Tkinter only; no third-party UI library |
| Group meeting check | Match on **exact name** + **exact duration (minutes)** |
| Conflict definition | Any overlap: `new.start < existing.end AND new.end > existing.start` |
| Replace = delete + add | Remove old appointment file, create new one |
| Join group meeting | Append current userId to `participants` list and re-save |
