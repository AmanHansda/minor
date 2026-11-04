# ChronosAI — Administrator University Timetable System

ChronosAI is an **administrator-only university timetable creation, constraint validation, and scheduling system** designed for departmental coordinators and the central University Timetable Office. It automates weekly schedule preparation across academic cohorts, faculty, and rooms while guaranteeing zero resource double-bookings.

---

## Key Architectural Choices

1. **Zero External Dependencies (Stdlib-First)**
   * Built entirely on Python’s standard library (`http.server.ThreadingHTTPServer`, `dataclasses`, `json`).
   * Runs out of the box with `python -m backend.app.main` without needing virtual environments or `pip install`.
2. **Decoupled Solver & Safety Validator (`validator.py` as Authority)**
   * **Generation is separated from validation**: Schedules are generated using a deterministic first-fit greedy heuristic, but an independent validator performs the final hard checks (H1–H9).
   * A timetable is marked `FEASIBLE` only when hard violations equal zero.
3. **Deterministic Soft Optimization & Candidate Ranking**
   * Candidate slots are scored deterministically: prioritizes instructor preferred slots (`teacher.preferred`), clusters cohort classes to eliminate dead idle gaps, and avoids un-preferred Period 1 fatigue.
   * Determinism ensures identical inputs always produce identical, explainable outputs during academic vivas and evaluations.
4. **Automated Teaching Batch Partitioning**
   * Connects **Course + Academic Group + Faculty + Weekly Hours + Teaching Type**:
     * **Full Class Lecture**: Whole cohort $\rightarrow$ Lecture Hall ($\text{capacity} \ge \text{students}$), 1-hour block.
     * **Tutorial Class**: Auto-divided into 3 batches $\rightarrow$ Classroom, 1-hour block, distinct batches may run in parallel.
     * **Laboratory**: Auto-divided into 2 batches $\rightarrow$ Specialized Lab, consecutive 2-hour blocks, strictly blocked from crossing lunch.
5. **Inviolable Fixed Lunch Interval (H7)**
   * Period 5 (1:00 PM – 2:00 PM) is globally reserved across all cohorts, instructors, and rooms.
6. **Anti-Slop Academic Console (Art Direction)**
   * Styled according to `design-taste-frontend` (`references/app-screens.md`): flat surfaces, crisp 1px borders, zero blurry card shadows, and restrained color reserved for data state (green for Feasible, crimson for Infeasible, amber for labs).
   * Formats official, print-ready weekly Day × Period grids (`@media print`) with university headers, course directories, and sign-off blocks.
7. **Read-Only Timetable QA Assistant & Minimal-Disruption Simulator**
   * **Timetable Chatbot**: Strictly read-only query engine over active schedule data; cannot modify data, call outside networks, or bypass validation.
   * **Absence Simulation**: Locks unaffected sessions in place and reallocates only the absent teacher's requirements.
8. **Comprehensive Export Architecture**
   * Master CSV, iCalendar (`.ics`), and per-entity schedule exports (`/api/export/class/...`, `/api/export/teacher/...`, `/api/export/room/...`).

---

## System Architecture

```text
frontend/index.html              Admin Single-Page Console (UI, Grids, QA Chat, Print Layouts)
backend/app/
  main.py                        HTTP API, routing, static server & input converter
  sample_data.py                 Bundled synthetic university demo dataset
  services.py                    Quality analytics, slot explanation, exports (CSV/iCal)
  storage.py                     Local JSON persistence (data/department_input.json)
  chatbot.py                     Rule-based read-only timetable QA assistant
  solver/
    models.py                    Domain objects (Room, Instructor, Requirement, Entry)
    engine.py                    Deterministic heuristic scheduler with preference scoring
    validator.py                 Single source of truth for hard constraints (H1–H9)
backend/tests/
  test_solver.py                 Automated test suite (9 unit tests passing)
docs/
  DECISIONS.md                   Architecture Decision Records (D1–D7)
  HANDOFF.md                     Operational handoff guide & maintenance invariants
  UNIVERSITY_OPERATING_MODEL.md  Academic workflow & institutional requirements
  report/PROJECT_REPORT.md       Comprehensive viva & academic project documentation
```

---

## Quickstart

### 1. Run the Application
Open a terminal in the project directory:

```powershell
python -m backend.app.main
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

### 2. Run Automated Tests
```powershell
python -m unittest discover -s backend/tests -v
```

---

## Implemented Constraints (H1–H9)

| Code | Constraint | Verification Mechanism |
|---|---|---|
| **H1** | Contact Hours & Block Size | Total scheduled hours match requirement; lab block lengths enforced. |
| **H2** | Cohort Non-Overlap | Full group blocks all sub-batches; distinct batches can run in parallel. |
| **H3** | Faculty Non-Overlap | Faculty cannot be scheduled in two locations at the same period. |
| **H4** | Room Non-Overlap | Physical room cannot host multiple simultaneous meetings. |
| **H5** | Room Type & Accessibility | Room type (`LECTURE`, `CLASSROOM`, `LAB`) and accessibility match needs. |
| **H6** | Room Seating Capacity | Seating capacity $\ge$ attending student strength. |
| **H7** | Lunch Break Inviolable | Period 5 (1:00 PM – 2:00 PM) is strictly protected; no sessions can cross lunch. |
| **H8** | Valid Grid & Availability | Monday–Friday Periods 1–8; instructor hard unavailable periods respected. |
| **H9** | Maximum Teaching Load | Total assigned hours $\le$ faculty weekly teaching cap. |

---

## Academic Scope & Roadmap

ChronosAI is a working **departmental pilot prototype**. It uses a deterministic greedy heuristic rather than an OR-Tools CP-SAT engine, and local JSON persistence rather than PostgreSQL. 

For full university-wide rollout:
1. Transition local JSON persistence to PostgreSQL with migrations.
2. Add role-based authentication and audit logs for timetable officers.
3. Replace the greedy engine with OR-Tools CP-SAT while retaining `validator.py` as the safety boundary.
4. Add bulk CSV/Excel data import templates.
5. Add timetable version rollback and publishing workflows.
