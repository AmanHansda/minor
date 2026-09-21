# ChronosAI

Chronos is a final-year B.Tech project that generates a clash-free weekly university timetable. It uses a deterministic constraint-aware greedy scheduler and a validator as the final safety check. The project deliberately keeps the first version simple enough to explain in a viva.

## Features included

- Course, instructor, cohort and room based scheduling
- Hard checks for clashes, room type/capacity, availability, breaks and lab blocks
- Soft quality score for early classes, instructor preferences and timetable gaps
- What-if comparison, teacher-absence rescheduling and explain-a-slot output
- Resilience, wellbeing, green-use and fairness indicators
- CSV and iCalendar export
- Timetable help chat that answers schedule, teacher and room questions from generated data
- Browser dashboard with synthetic demo data

## Run locally

No external package is needed for the demonstrator. From the project folder:

```powershell
python -m backend.app.main
```

Open http://127.0.0.1:8000. The dashboard loads the bundled demo and lets you generate a timetable.

## Test

```powershell
python -m unittest discover -s backend/tests -v
```

## Honest scope

This version is a working academic prototype. It uses a deterministic greedy heuristic rather than a full CP-SAT engine, and stores demo data in JSON rather than PostgreSQL. The chat assistant only reads the current timetable; it never changes it. See `docs/DECISIONS.md` and `docs/report/PROJECT_REPORT.md`.

## Continuing the project

Give the next coding agent [the handoff guide](docs/HANDOFF.md). It explains the intended administrator-only workflow, completed code, gaps, production roadmap and a ready-to-paste next-task prompt.
