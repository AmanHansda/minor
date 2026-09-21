# Chronos Department Pilot Deployment

## What is ready now

The application accepts department data through the Administrator workspace, saves it locally in `data/department_input.json`, produces a validated weekly schedule, presents separate Admin, Teacher and Student views, exports CSV/iCalendar, and provides a read-only timetable assistant.

## Run

From the folder that contains `backend` and `frontend`:

```powershell
python -m backend.app.main
```

Open `http://127.0.0.1:8000`.

## Pilot workflow

1. Administrator loads the sample data or enters rooms, teachers and classes.
2. Administrator clicks **Save Input Data** and then **Generate Whole Timetable**.
3. Review the FEASIBLE status and hard-violation count.
4. Teacher selects their own name in Teacher View.
5. Student selects their class section in Student View.
6. Export the approved timetable.

## Before university-wide production deployment

Use a managed PostgreSQL database, institution login/SSO, HTTPS, role permissions, backups, change audit logs, data import approval, load testing and an OR-Tools CP-SAT scheduler. These are operational requirements for a university rollout; the current package is a functional departmental pilot, not a multi-user production service.
