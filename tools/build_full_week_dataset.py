"""Build a complete Mon-Fri 9am-5pm (35 hours/week per cohort) full-timetable dataset."""
import sys
from pathlib import Path
import json
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app import xlsx_io, main
from backend.app.solver.engine import generate
from backend.app.solver.validator import validate, DAYS, PERIODS


def build_full_week_dataset():
    groups = [
        ["CSE-S3-A", "CSE", "B.Tech", "2nd Year", "A", 60],
        ["CSE-S3-B", "CSE", "B.Tech", "2nd Year", "B", 60],
    ]

    rooms = [
        ["LH1", "Lecture Hall 1", "LECTURE", 80, "Academic Block", "CSE", "TRUE"],
        ["LH2", "Lecture Hall 2", "LECTURE", 80, "Academic Block", "CSE", "TRUE"],
        ["CR1", "Tutorial Room 1", "CLASSROOM", 60, "Academic Block", "CSE", "TRUE"],
        ["CR2", "Tutorial Room 2", "CLASSROOM", 60, "Academic Block", "CSE", "TRUE"],
        ["LAB1", "Computing Lab 1", "LAB", 60, "Lab Block", "CSE", "TRUE"],
        ["LAB2", "Computing Lab 2", "LAB", 60, "Lab Block", "CSE", "TRUE"],
    ]

    faculty = [
        ["T1", "Dr. Alan Turing", 24, "", "Mon-1, Wed-1"],
        ["T2", "Dr. Grace Hopper", 24, "", "Mon-2, Thu-2"],
        ["T3", "Dr. Donald Knuth", 24, "", "Tue-1, Wed-2"],
        ["T4", "Dr. Ada Lovelace", 24, "", "Tue-2, Thu-1"],
        ["T5", "Dr. John von Neumann", 24, "", "Mon-3, Fri-1"],
        ["T6", "Dr. Claude Shannon", 24, "", "Wed-3, Fri-2"],
        ["T7", "Dr. Barbara Liskov", 24, "", "Tue-4, Thu-3"],
        ["T8", "Dr. Linus Torvalds", 24, "", "Mon-1, Wed-1"],
        ["T9", "Dr. Margaret Hamilton", 24, "", "Mon-2, Thu-2"],
        ["T10", "Dr. Ken Thompson", 24, "", "Tue-1, Wed-2"],
        ["T11", "Dr. Leslie Lamport", 24, "", "Tue-2, Thu-1"],
        ["T12", "Dr. Edsger Dijkstra", 24, "", "Mon-3, Fri-1"],
        ["T13", "Dr. Tim Berners-Lee", 24, "", "Wed-3, Fri-2"],
        ["T14", "Dr. Vint Cerf", 24, "", "Tue-4, Thu-3"],
    ]

    allocations = [
        # Section A allocations (35 hours total = 7 periods * 5 days)
        ["CS301", "Data Structures", "CSE-S3-A", "T1", "CLASS", 5, 1, "FALSE"],
        ["CS302", "Computer Organization", "CSE-S3-A", "T2", "CLASS", 4, 1, "FALSE"],
        ["CS303", "Database Systems", "CSE-S3-A", "T3", "CLASS", 5, 1, "FALSE"],
        ["CS304", "Operating Systems", "CSE-S3-A", "T4", "CLASS", 4, 1, "FALSE"],
        ["CS305", "Discrete Mathematics", "CSE-S3-A", "T5", "CLASS", 5, 1, "FALSE"],
        ["CS306", "Software Engineering", "CSE-S3-A", "T6", "CLASS", 2, 1, "FALSE"],
        ["CS307", "Theory of Computation", "CSE-S3-A", "T7", "CLASS", 1, 1, "FALSE"],
        ["CS308", "Data Structures Lab", "CSE-S3-A", "T1", "CLASS", 2, 2, "FALSE"],
        ["CS309", "Database Systems Lab", "CSE-S3-A", "T3", "CLASS", 2, 2, "FALSE"],
        ["CS310", "Linux Kernel Lab", "CSE-S3-A", "T4", "CLASS", 2, 2, "FALSE"],
        ["HS301", "Technical Communication", "CSE-S3-A", "T6", "CLASS", 2, 1, "FALSE"],
        ["CS311", "Academic Seminar", "CSE-S3-A", "T7", "CLASS", 1, 1, "FALSE"],

        # Section B allocations (35 hours total = 7 periods * 5 days)
        ["CS301", "Data Structures", "CSE-S3-B", "T8", "CLASS", 5, 1, "FALSE"],
        ["CS302", "Computer Organization", "CSE-S3-B", "T9", "CLASS", 4, 1, "FALSE"],
        ["CS303", "Database Systems", "CSE-S3-B", "T10", "CLASS", 5, 1, "FALSE"],
        ["CS304", "Operating Systems", "CSE-S3-B", "T11", "CLASS", 4, 1, "FALSE"],
        ["CS305", "Discrete Mathematics", "CSE-S3-B", "T12", "CLASS", 5, 1, "FALSE"],
        ["CS306", "Software Engineering", "CSE-S3-B", "T13", "CLASS", 2, 1, "FALSE"],
        ["CS307", "Theory of Computation", "CSE-S3-B", "T14", "CLASS", 1, 1, "FALSE"],
        ["CS308", "Data Structures Lab", "CSE-S3-B", "T8", "CLASS", 2, 2, "FALSE"],
        ["CS309", "Database Systems Lab", "CSE-S3-B", "T10", "CLASS", 2, 2, "FALSE"],
        ["CS310", "Linux Kernel Lab", "CSE-S3-B", "T11", "CLASS", 2, 2, "FALSE"],
        ["HS301", "Technical Communication", "CSE-S3-B", "T13", "CLASS", 2, 1, "FALSE"],
        ["CS311", "Academic Seminar", "CSE-S3-B", "T14", "CLASS", 1, 1, "FALSE"],
    ]

    config = [["13:00"]]
    return groups, rooms, faculty, allocations, config


def generate_and_save():
    groups, rooms, faculty, allocations, config = build_full_week_dataset()

    xlsx_io.SAMPLES.update({
        "Groups": groups,
        "Rooms": rooms,
        "Faculty": faculty,
        "Allocations": allocations,
        "Configuration": config,
    })

    # Save to Excel
    target_xlsx = ROOT / "outputs" / "full_week_timetable_dataset" / "chronosai_full_week_mon_fri_dataset.xlsx"
    target_xlsx.parent.mkdir(parents=True, exist_ok=True)
    workbook_bytes = xlsx_io.build_template()
    target_xlsx.write_bytes(workbook_bytes)

    # Validate upload parser
    data = xlsx_io.parse_upload(workbook_bytes)
    assert len(data["class_groups"]) == 2
    assert len(data["rooms"]) == 6
    assert len(data["instructors"]) == 14
    assert len(data["requirements"]) == 24

    # Validate solver can schedule full week
    reqs, rms, ppl = main.read_data(data)
    sched = generate(reqs, rms, ppl, lunch_period=5)
    assert sched.status == "FEASIBLE", f"Solver failed: {sched.messages}"

    errors = validate(sched.entries, reqs, rms, ppl, lunch_period=5)
    assert not errors, f"Validation errors: {errors}"

    # Verify 100% full grid coverage (every period except lunch P5 for Mon-Fri)
    for cohort in ["CSE-S3-A", "CSE-S3-B"]:
        cohort_entries = [e for e in sched.entries if e.cohort == cohort]
        occupied_slots = set()
        for e in cohort_entries:
            for p in range(e.period, e.period + e.length):
                occupied_slots.add((e.day, p))
        missing = [(d, p) for d in DAYS for p in [1, 2, 3, 4, 6, 7, 8] if (d, p) not in occupied_slots]
        assert len(missing) == 0, f"Cohort {cohort} has missing slots: {missing}"

    # Also persist to data/department_input.json and .local.json so the app uses it
    json_payload = {
        "requirements": [r.__dict__ for r in reqs],
        "rooms": [r.__dict__ for r in rms],
        "instructors": [i.__dict__ for i in ppl],
        "class_groups": data["class_groups"],
        "config": {"lunch_time": "13:00"},
    }
    input_file = ROOT / "data" / "department_input.json"
    local_file = ROOT / "data" / "department_input.local.json"
    input_file.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")
    if local_file.exists():
        local_file.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")

    # If local server is running, update its active in-memory state
    try:
        req = urllib.request.Request(
            "http://localhost:8000/api/data",
            data=json.dumps(json_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=3)
        # Also trigger generation
        urllib.request.urlopen("http://localhost:8000/api/generate", timeout=5)
        print("Updated running local server at http://localhost:8000 successfully.")
    except Exception as e:
        print(f"Server notify skipped: {e}")

    print(f"Generated: {target_xlsx}")
    print(f"Verified: 2 cohorts, 70 placed hours across 5 days (Mon-Fri 09:00 - 17:00).")
    print(f"Status: FEASIBLE, 0 violations, 0 missing slots.")


if __name__ == "__main__":
    generate_and_save()
