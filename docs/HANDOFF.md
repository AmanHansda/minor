# Chronos Project Handoff Guide

## Purpose

Chronos is an **administrator-only university timetable builder**. It is not a student or teacher portal.

Read `docs/UNIVERSITY_OPERATING_MODEL.md` before modifying the project. It is the agreed academic workflow and role model.

The administrator must be able to:

1. Create academic groups: B.Tech 1st-4th year, M.Tech 1st-2nd year, and PhD 1st-2nd year; each with department, section and student count.
2. Create department-owned classrooms and laboratories with room number, block, room type and seating capacity.
3. Create faculty records, teaching load, unavailable periods and preferred periods.
4. Assign a faculty member to teach a subject for an academic group, with contact hours, block length and room type.
5. Generate a clash-free weekly timetable.
6. Preview/export timetable sheets by academic group, faculty and classroom/laboratory.

Student and teacher sheets are **outputs prepared by the administrator**. The project must not claim to implement student login or teacher login.

## Current architecture

```text
frontend/index.html              Administrator single-page interface
backend/app/main.py              HTTP API and input conversion
backend/app/solver/engine.py     Deterministic greedy timetable generator
backend/app/solver/validator.py  Hard-constraint safety checks
backend/app/solver/models.py     Room, Instructor, Requirement, Entry data objects
backend/app/services.py          Quality report, absence flow and exports
backend/app/chatbot.py           Read-only timetable helper
backend/app/storage.py           Local JSON persistence for pilot data
backend/tests/test_solver.py     Automated tests
docs/constraints.md              Constraint documentation
docs/PILOT_DEPLOYMENT.md         Pilot deployment guidance
```

## Run the project

Open a terminal in the folder containing `backend` and `frontend`.

```powershell
python -m backend.app.main
```

Open `http://127.0.0.1:8000`.

Run tests before and after every change:

```powershell
python -m unittest discover -s backend/tests -v
```

## Current completed functionality

- Admin data entry for academic groups, rooms/labs, teachers and course allocations.
- Room records include type, capacity, block and allocated department.
- Teacher records include max weekly load and unavailable slots; the UI also captures preferred slots.
- A requirement connects **subject + group + faculty + student strength + weekly hours + room type**.
- Generator blocks overlapping faculty, academic-group and room allocations.
- Validator checks required hours, room type/capacity, break periods, availability and faculty weekly load.
- Class-sheet format resembles a formal university weekly grid with a subject/faculty directory.
- Teacher schedule preview and full administrative timetable table exist.
- CSV and iCalendar exports exist.
- Input is stored locally at `data/department_input.json` after Save Input Data.

## Known gaps and highest-priority next work

1. **Finish classroom sheet preview.** The HTML has a Classroom Sheet Preview tab but the JavaScript must populate its selector and filter schedule entries by room. Implement `renderRoom()` and call it from `renderSchedules()`.
2. **Make the edit experience clearer.** Current Add or Update buttons replace an item when the same ID is entered. Add Edit buttons in each admin table that load a chosen record back into its form. Add confirmation before deleting records.
3. **Use faculty preferences in the objective.** `Instructor.preferred` is captured but `services.quality_report` and `solver/engine.py` do not yet favour those slots. Add a soft score without weakening hard validation.
4. **Persist class groups fully.** `class_groups` are accepted by the API and retained during the running session. Extend `storage.py` so groups reload after restart.
5. **Add separate exports.** Add `/api/export/class/<group>`, `/api/export/teacher/<id>` and `/api/export/room/<id>` for printable CSV/PDF files.
6. **Add delete and validation UI.** Prevent duplicate IDs in the browser, validate positive capacity/hours, and display errors next to the relevant form.

## Production roadmap

Do not call the present package university-wide production-ready. It is a department pilot. For production, implement in this order:

1. Replace JSON persistence with PostgreSQL and migrations.
2. Add secure administrator authentication, roles, audit logging and backups.
3. Replace greedy scheduling with OR-Tools CP-SAT while keeping `validator.py` as the final safety check.
4. Add import templates for rooms, faculty, academic groups and teaching allocations.
5. Add timetable versions, approval/publish flow and rollback.
6. Add PDF/XLSX/iCalendar exports for class, teacher and room.
7. Perform institutional data-security review, HTTPS deployment, load testing and user acceptance testing.

## Important invariants

- `validator.py` is the final authority. Do not let a UI edit, importer or assistant bypass it.
- A timetable entry must never overlap by group, faculty or room.
- A room must match both capacity and required room type.
- Labs must use consecutive periods and cannot cross lunch.
- The read-only chat helper can answer questions but must never modify schedules.
- Do not introduce external AI features unless specifically requested. The current project needs reliable timetable functionality first.

## Safe task sequence for the next agent

1. Read this file, `README.md`, `docs/constraints.md` and the files in `backend/app/solver/`.
2. Run the tests and start the application.
3. Complete one small feature at a time.
4. Add a unit test for each new hard constraint or API rule.
5. Run all tests after every implementation batch.
6. Update `docs/DECISIONS.md` when making a non-obvious design decision.
7. Do not remove working validation simply to make a difficult sample dataset schedule.

## Suggested next Codex prompt

```text
Read docs/HANDOFF.md completely. Continue Chronos as an administrator-only university timetable builder. First run the existing unit tests. Implement the Classroom Sheet Preview end to end: populate the room selector from admin room records, filter the generated timetable by room, render a formal weekly grid, and add a test that generated entries never overlap for a selected room. Preserve validator.py as the safety boundary. Do not add student or teacher login features and do not add AI features.
```
