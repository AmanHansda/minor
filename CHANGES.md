# Chronos Timetable Generation System — Modification & Audit Log

**Project:** University Timetable Scheduling System (Departmental Pilot)  
**Date of Audit & Fixes:** November 2026  
**Status:** All Unit Tests Passing (13/13) · All End-to-End Integration Tests Passing (10/10) · 0 Hard Clashes

---

## 1. Executive Summary

A comprehensive end-to-end audit was conducted across the backend solver engine, service layer, data persistence layer, HTTP API routes, automated test suite, and the frontend single-page administrative console.

All identified flaws—including data degradation on save, duplicate batch expansions, absence simulation failures, chatbot limitations, invalid iCalendar RFC formatting, and form lifecycle defects—have been corrected and verified with automated test suites.

---

## 2. Summary of Identified Flaws & Fixes

| # | Flaw | Root Cause | Fix Implemented |
|---|---|---|---|
| **1** | **Labs Degraded to Lectures; Lab Rooms Sat Empty** | In `read_data()`, requirements lacking an explicit `allocation_type` defaulted to `"CLASS"` which forced `room_type = "LECTURE"`. All labs in `department_input.json` became `LECTURE`, competing for the single lecture hall while computer labs remained unused. | Added `allocation_type: Optional[str] = None` to `Requirement` domain model. Updated `read_data()` to preserve existing `room_type` and infer `allocation_type` from room/course properties. |
| **2** | **Exponential Batch Re-splitting on Save** | Saving an already-partitioned batch (`::LAB-1`, `[LAB Group 1]`) caused `read_data()` to partition it again into `::LAB-1::LAB-1`, doubling sessions on every save. | Implemented batch detection regex (`::`, ` [`, or `[-_:]b\d+`) in `read_data()` to prevent re-partitioning already-expanded batches. |
| **3** | **Absence Simulation Always Failed or Rescheduled Absent Teacher** | `absent_reschedule()` passed only the absent teacher's requirements to `generate()`, causing `validator.py` to reject all kept sessions as `Unknown requirement`. Furthermore, `engine.py` re-scheduled all hours regardless of locked entries. | Updated `engine.py` to deduct locked hours (`remaining = req.hours - placed_hours`), reallocated absent teacher's workload to available substitute faculty with remaining capacity, and passed full requirements to `validate()`. |
| **4** | **"Reload Demo Data" Failed to Reset State** | `GET /api/demo` loaded whatever data was in `department_input.json`. Clicking "Reload Demo Data" re-returned existing edited data instead of the pristine sample dataset. | Added `?reset=1` query parameter handling to `GET /api/demo` to reset in-memory state, reload from `sample_data.py`, and persist clean records. |
| **5** | **Cohort Mismatch on Class Timetable Sheet** | Sample requirements had cohort `CSE-S3-A`, but `formatGroupId()` generated `CSE-BTech-3rdYear-A`. The class sheet dropdown defaulted to an empty grid on initial generation. | Allowed custom/explicit `Group Code` input, updated `formatGroupId()` to prioritize `g.code || g.id`, and added base-cohort normalization (`getBaseCohort()`) so all sub-batches (`CSE-S3-A`, `CSE-S3-A::LAB-1`, `CSE-S3-A-B1`) render correctly. |
| **6** | **Brittle QA Chatbot** | "Where is Data Structures?" only returned the first slot found (ignoring remaining days); room queries listed all weekly bookings without answering for the requested day; teacher IDs (`I1`) were unhandled. | Enhanced `chatbot.py` to aggregate all weekly slots for courses, support lookup by instructor ID/name, parse day/period room queries ("Is LAB1 free on Monday period 1?"), and handle lunch break/clash queries. |
| **7** | **Form Inputs Not Reset on Submit/Cancel** | Submitting or canceling an edit in Academic Groups, Rooms, Faculty, or Allocations left previous values in input fields, requiring manual deletion before entering the next record. | Added automatic input reset logic in `index.html` after successful addition and inside `cancelEdit()`. |
| **8** | **Unprotected Export Endpoints (400 JSON Error in New Tabs)** | Clicking CSV or iCalendar exports before timetable generation caused new blank browser tabs to open displaying raw JSON errors. | Added validation guards in both frontend (`showNotice` guard) and backend (clean HTTP 400 JSON instead of 404 static fallback). |
| **9** | **iCalendar (`.ics`) Start Dates Discrepancy** | `export_ical` hardcoded `DTSTART:20260105` (Monday) for all events, violating RFC 5545 recurrence rules for Tuesday–Friday classes. | Mapped each weekday to its corresponding calendar date (`Mon` $\rightarrow$ `20260105`, `Tue` $\rightarrow$ `20260106`, `Wed` $\rightarrow$ `20260107`, `Thu` $\rightarrow$ `20260108`, `Fri` $\rightarrow$ `20260109`). |
| **10** | **Multi-Hour Lab Display Clutter** | In weekly grids, consecutive 2-hour labs showed identical full cards in each period, looking like two duplicate classes. | Added continuation indicators (`↳ Data Structures Lab (cont. in LAB1)`) for subsequent periods. |
| **11** | **Teacher Availability Case Sensitivity** | Entering slots as `mon-1` or `monday-1` was ignored by `validator.py` because it strictly looked for `"Mon-1"`. | Added slot normalization regex in frontend to standardize user input to title-case `Day-Period` (`Mon-1`, `Tue-2`). |
| **12** | **Faculty Workload Fairness Metric Distortion** | Faculty members with 0 assigned hours were omitted from `loads` in `quality_report()`, artificially skewing the Gini coefficient and fairness metric. | Initialized all department instructors in `by_teacher` so unassigned faculty count in workload fairness calculations. |

---

## 3. Detailed Component Modifications

### 3.1 `minor/backend/app/solver/models.py`
* Added `allocation_type: Optional[str] = None` to the `Requirement` dataclass.
* Ensures serialization and deserialization via `storage.py` preserves teaching type (`CLASS`, `TUTORIAL`, `LAB`).

### 3.2 `minor/backend/app/solver/engine.py`
* Fixed `generate()` when handling locked entries:
  ```python
  placed_hours = sum(e.length for e in entries if e.requirement_id == req.id)
  remaining = req.hours - placed_hours
  if remaining <= 0:
      continue
  ```
* Prevents placing duplicate hours for locked entries while allowing the validator to verify the complete requirement set.

### 3.3 `minor/backend/app/sample_data.py`
* Assigned explicit `allocation_type` and appropriate `room_type` to all demo requirements:
  * `R1` (Data Structures): `room_type="LECTURE"`, `allocation_type="CLASS"`
  * `R2` (Data Structures Lab B1): `room_type="LAB"`, `allocation_type="LAB"`
  * `R3` (Data Structures Lab B2): `room_type="LAB"`, `allocation_type="LAB"`
  * `R4` (Discrete Mathematics): `room_type="LECTURE"`, `allocation_type="CLASS"`
  * `R5` (Database Systems): `room_type="CLASSROOM"`, `allocation_type="CLASS"`
  * `R6` (Database Lab): `room_type="LAB"`, `allocation_type="LAB"`
* Added `load_demo_groups()` returning `[{"code": "CSE-S3-A", "program": "B.Tech", "year": "3rd Year", "section": "A", "students": 60, "department": "CSE"}]`.

### 3.4 `minor/backend/app/services.py`
* **`absent_reschedule()`**:
  * Identifies affected entries taught by the absent faculty.
  * Identifies candidate substitute faculty with remaining capacity (`loads + req.hours <= max_hours_week`).
  * Reassigns requirements to the best available substitute.
  * Locks all unaffected sessions in place and runs `generate()`.
  * Returns detailed diff message, substitute names, and reassignment list.
* **`quality_report()`**:
  * Initialized all instructors with `by_teacher.setdefault(i.id, 0)` so unassigned faculty count toward Gini fairness.
* **`export_csv()`**:
  * Added RFC-compliant CSV quotes around string fields.
* **`export_ical()`**:
  * Added weekday-to-date mapping (`Mon`: `20260105`, `Tue`: `20260106`, `Wed`: `20260107`, `Thu`: `20260108`, `Fri`: `20260109`) to ensure `DTSTART` matches `RRULE:FREQ=WEEKLY;BYDAY=...`.

### 3.5 `minor/backend/app/chatbot.py`
* **Course queries**: Aggregates all weekly sessions for a course and returns day, period, room, and cohort.
* **Faculty queries**: Matches by full name, last name, or faculty ID (e.g. `I1`, `T1`).
* **Room availability**: Parses specific day and period queries (e.g., "Is LAB1 free on Monday period 1?") to report exact status; reports general booked and free periods when no slot is specified.
* **Lunch queries**: Explains that Period 5 (1:00 PM – 2:00 PM) is the fixed lunch interval.
* **Feasibility queries**: Reports total placed sessions and hard violation status.

### 3.6 `minor/backend/app/main.py`
* **`read_data()`**:
  * Preserves existing `room_type` when `allocation_type == "CLASS"` (does not force `"LECTURE"`).
  * Detects already-partitioned requirements (`::`, ` [`, `[-_:]b\d+`) to prevent re-splitting.
  * Populates `allocation_type` on created `Requirement` objects.
* **`do_GET()`**:
  * `GET /api/demo?reset=1`: Resets state and reloads pristine demo data.
  * `GET /api/data`: Returns current saved data or demo data.
  * `GET /api/explain/<idx>`: Returns HTTP 400 JSON when schedule is not generated yet (instead of 404 static file fallback).
  * `GET /api/absence/<ident>`: Returns HTTP 400 JSON when schedule is not generated yet.

### 3.7 `minor/data/department_input.json`
* Regenerated with clean initial data:
  * Restored `room_type: "LAB"` for R2, R3, R6.
  * Restored `room_type: "CLASSROOM"` for R5.
  * Restored `allocation_type` properties.
  * Included `code: "CSE-S3-A"` in `class_groups`.

### 3.8 `minor/frontend/index.html`
* **Card 1 (Academic Groups)**: Added `Group Code (Optional)` input field.
* **`formatGroupId()`**: Prioritizes `g.code || g.id`.
* **Form CRUD**: Added input clearing on addition and cancellation across groups, rooms, faculty, and allocations.
* **`normalizeSlot()`**: Auto-converts inputs like `mon-1`, `Monday-2` to title-case `Mon-1`, `Mon-2`.
* **`deleteRecord()`**: Added active-edit cancellation and foreign-key check warnings when deleting assigned faculty or rooms.
* **`openPanel()`**: Automatically calls `renderStudentSheet()`, `renderTeacherSheet()`, or `renderRoomSheet()` on tab switch.
* **`buildWeeklyGrid()`**: Shows `↳ <Course> (cont. in <Room>)` for continuation periods of multi-hour labs.
* **`simulateAbsence()`**: Renders detailed substitution results and outcome status.
* **Export buttons**: Guarded against clicking before timetable generation.

### 3.9 `minor/backend/tests/test_solver.py`
* Expanded test suite from 9 to 13 tests:
  1. `test_demo_solves_without_violations`
  2. `test_validator_detects_room_conflict`
  3. `test_quality_has_required_indicators`
  4. `test_chat_answers_course_question`
  5. `test_chat_answers_various_questions` *(new)*
  6. `test_input_payload_is_converted_to_domain_data`
  7. `test_tutorial_and_lab_are_expanded_into_groups`
  8. `test_read_data_preserves_room_types_on_resave` *(new)*
  9. `test_full_class_conflicts_with_lab_batch_but_distinct_batches_can_overlap`
  10. `test_per_entity_exports`
  11. `test_ical_export_rfc_compliance` *(new)*
  12. `test_generated_schedule_never_has_room_overlap`
  13. `test_absent_reschedule_preserves_unaffected_and_reassigns_cleanly` *(new)*

---

## 4. Button-by-Button Verification Matrix

| UI Panel / Section | Button / Control | Action Triggered | Verified Behavior |
|---|---|---|---|
| **Top Bar** | Status Badge | Reactive display | Shows "Feasible · 0 Violations (12 sessions placed)" in green. |
| **Top Navigation** | Tabs (Admin, Student, Teacher, Room, Absence/Chat) | `openPanel(name)` | Activates target panel and renders fresh data immediately. |
| **Master Controls** | `▶ Generate Whole Timetable` | `saveAndGenerate()` | Persists data, generates schedule, updates metrics, renders sheets. |
| **Master Controls** | `💾 Save Input Data` | `saveData()` | Sends JSON payload to `/api/data`; preserves room types and allocations. |
| **Master Controls** | `↺ Reload Demo Data` | `loadDemo(true)` | Calls `/api/demo?reset=1`, restores pristine dataset, resets UI state. |
| **Master Controls** | `Export Master CSV` | `downloadExport('csv')` | Downloads `timetable_master.csv` with properly quoted fields. |
| **Master Controls** | `Export iCalendar (.ics)` | `downloadExport('ical')` | Downloads `timetable.ics` with RFC-compliant weekday start dates. |
| **Academic Groups** | `Add Academic Group` | `saveGroup()` | Adds group, supports custom code (e.g. `CSE-S3-A`), clears form. |
| **Academic Groups** | `Edit` (Table row) | `editRecord('group', i)` | Displays editing banner, loads fields into form, switches button to "Update". |
| **Academic Groups** | `Cancel` (Banner) | `cancelEdit('group')` | Hides editing banner, clears inputs, resets button to "Add". |
| **Academic Groups** | `Delete` (Table row) | `deleteRecord('group', i)` | Confirms deletion, removes group, clears active edit if matching. |
| **Classrooms & Labs** | `Add Room` | `saveRoom()` | Adds facility, enforces ID, clears form inputs. |
| **Classrooms & Labs** | `Edit` / `Delete` / `Cancel` | Table row buttons | Fully operational with cascade warning. |
| **Faculty Records** | `Add Faculty` | `saveTeacher()` | Normalizes availability slots (`mon-1` $\rightarrow$ `Mon-1`), clears inputs. |
| **Faculty Records** | `Edit` / `Delete` / `Cancel` | Table row buttons | Warns if faculty member is assigned to course allocations. |
| **Allocations** | `Teaching Type` dropdown | `onchange` | Auto-sets block size (2 for LAB, 1 for CLASS) and facility type. |
| **Allocations** | `Add Allocation` | `saveAllocation()` | Validates inputs, assigns room type, clears form inputs. |
| **Allocations** | `Edit` / `Delete` / `Cancel` | Table row buttons | Fully operational. |
| **Master Schedule** | Row click / `Explain` | `inspectSlot(idx)` | Opens modal showing allocation details and the 6 hard checks passed. |
| **Master Schedule** | `✕` Modal Close | `closeModal()` | Closes slot explanation modal (also closes on overlay click). |
| **Class Sheet** | Cohort Select dropdown | `renderStudentSheet()` | Displays Day × Period grid for all lectures and lab batches. |
| **Class Sheet** | `🖨 Print Official Sheet` | `window.print()` | Formats print-ready sheet with official header and sign-off block. |
| **Class Sheet** | `Export Class CSV` | `exportActiveEntity('class')` | Downloads cohort-specific CSV schedule. |
| **Faculty Sheet** | Faculty Select dropdown | `renderTeacherSheet()` | Displays weekly teaching grid and workload hours count. |
| **Faculty Sheet** | `🖨 Print Faculty Sheet` | `window.print()` | Isolates faculty schedule for official distribution. |
| **Faculty Sheet** | `Export Teacher CSV` | `exportActiveEntity('teacher')` | Downloads faculty-specific CSV schedule. |
| **Room Sheet** | Room Select dropdown | `renderRoomSheet()` | Displays room booking grid and utilization percentage. |
| **Room Sheet** | `🖨 Print Room Sheet` | `window.print()` | Isolates room utilization schedule. |
| **Room Sheet** | `Export Room CSV` | `exportActiveEntity('room')` | Downloads room-specific CSV schedule. |
| **Absence Card** | `Simulate Absence` | `simulateAbsence()` | Reallocates absent teacher's sessions to qualified faculty; locks others. |
| **QA Chatbot** | Suggestion Chips (4 chips) | `askPreset(...)` | Injects preset query and immediately sends to `/api/chat`. |
| **QA Chatbot** | Input Box (<kbd>Enter</kbd>) & `Send` | `sendChat()` | Sends message to read-only chatbot, appends question and answer to log. |

---

## 5. Verification Test Output

### 5.1 Backend Unit Test Suite (13/13 Passing)
```powershell
python -m unittest discover -s minor/backend/tests -v
```
```text
test_absent_reschedule_preserves_unaffected_and_reassigns_cleanly ... ok
test_chat_answers_course_question .............................. ok
test_chat_answers_various_questions ............................ ok
test_demo_solves_without_violations ............................ ok
test_full_class_conflicts_with_lab_batch_but_distinct_batches_can_overlap ... ok
test_generated_schedule_never_has_room_overlap ................. ok
test_ical_export_rfc_compliance ................................ ok
test_input_payload_is_converted_to_domain_data ................. ok
test_per_entity_exports ........................................ ok
test_quality_has_required_indicators ........................... ok
test_read_data_preserves_room_types_on_resave .................. ok
test_tutorial_and_lab_are_expanded_into_groups ................. ok
test_validator_detects_room_conflict ........................... ok

----------------------------------------------------------------------
Ran 13 tests in 0.008s - OK
```

### 5.2 End-to-End Server Integration Suite (10/10 Passing)
* Tested live HTTP serving of `index.html` (HTTP 200).
* Tested health, reset demo, saved data retrieval.
* Tested saving data and schedule generation (FEASIBLE, 0 hard violations, 3+ distinct rooms used).
* Tested slot inspector (`/api/explain/0`).
* Tested absence simulation with reallocation (`/api/absence/I1`).
* Tested Master CSV, iCal, Class CSV, Teacher CSV, and Room CSV exports.
* Tested QA chatbot across course, instructor, room availability, lunch break, clash queries, and help.
* Tested error handling (out of bounds explain $\rightarrow$ HTTP 400; invalid payload $\rightarrow$ HTTP 400).

