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
frontend/index.html              Administrator single-page interface (anti-slop academic console)
backend/app/main.py              HTTP API, routing, static serving and input conversion
backend/app/solver/engine.py     Deterministic greedy timetable generator with preference & gap optimization
backend/app/solver/validator.py  Hard-constraint safety checks (H1-H9 single source of truth)
backend/app/solver/models.py     Room, Instructor, Requirement, Entry data objects
backend/app/services.py          Quality report, slot explanation, absence flow, CSV/iCal/entity exports
backend/app/chatbot.py           Read-only timetable help assistant
backend/app/storage.py           Local JSON persistence for pilot data
backend/tests/test_solver.py     Automated test suite (9 unit tests passing)
docs/constraints.md              Constraint documentation
docs/DECISIONS.md                Key architectural design decisions (D1-D7)
docs/PILOT_DEPLOYMENT.md         Pilot deployment guidance
docs/UNIVERSITY_OPERATING_MODEL.md Agreed university operating rules
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

## Completed functionality

- Admin data entry for academic groups, rooms/labs, faculty and course allocations with clear edit and delete workflows.
- Room records include type, capacity, block and allocated department.
- Faculty records include max weekly load, hard unavailable slots and soft preferred slots.
- Automatic teaching allocations: Full Class Lecture (whole group, lecture hall), Tutorial (3 groups, classroom), Laboratory (2 groups, lab, consecutive 2h blocks).
- Generator blocks overlapping faculty, academic-group and room allocations.
- Validator checks required hours, room type/capacity, break periods (1-2 PM lunch), availability and faculty weekly load.
- Preference and gap optimization: `engine.py` scores candidate slots favoring instructor preferences and minimizing cohort idle gaps.
- Quality report tracks hard violations, gaps, early periods, fairness (Gini), resilience score, green score, and faculty preference satisfaction.
- Universal Weekly Day × Period Grids:
  1. **Academic Class Sheet**: Formal university weekly grid with lunch column and course/faculty directory.
  2. **Faculty Timetable Sheet**: Weekly grid with workload metrics and assigned classes.
  3. **Classroom/Lab Sheet**: Weekly grid with capacity utilization and clash verification.
- Interactive Slot Inspector: Click any session cell to inspect constraint validation details (`/api/explain/<idx>`).
- Interactive Timetable Assistant QA Chatbot: In-dashboard query interface with quick-action chips.
- Teacher Absence What-If simulation with minimal-disruption rescheduling.
- Master CSV, iCalendar (.ics), and per-entity CSV exports (`/api/export/class/<cohort>`, `/api/export/teacher/<id>`, `/api/export/room/<id>`).
- Print stylesheets (`@media print`) for official distribution sheets.
- Input data persistence in `data/department_input.json`.

## Production roadmap

Do not call the present package university-wide production-ready. It is a department pilot. For production, implement in this order:

1. Replace JSON persistence with PostgreSQL and migrations.
2. Add secure administrator authentication, roles, audit logging and backups.
3. Replace greedy scheduling with OR-Tools CP-SAT while keeping `validator.py` as the final safety check.
4. Add bulk CSV/Excel import templates for rooms, faculty, academic groups and teaching allocations.
5. Add timetable versions, approval/publish flow and rollback.
6. Add official PDF export generator for class, teacher and room sheets.
7. Perform institutional data-security review, HTTPS deployment, load testing and user acceptance testing.

## Important invariants

- `validator.py` is the final authority. Do not let a UI edit, importer or assistant bypass it.
- A timetable entry must never overlap by group, faculty or room.
- A room must match both capacity and required room type.
- Labs must use consecutive periods and cannot cross lunch.
- The read-only chat helper can answer questions but must never modify schedules.
- Do not introduce external AI features unless specifically requested. The current project needs reliable timetable functionality first.
