"""Single source of truth for timetable safety rules."""
from collections import defaultdict
import re
from .models import Entry, Requirement, Room, Instructor

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
# 9am to 5pm with period 5 (1pm to 2pm) reserved for lunch.
PERIODS = range(1, 9)
BREAKS = {5}

# Matches any automatic batch suffix added during expansion:
#   ::LAB-1  ::TUTORIAL-2  -B1  -B2  _B3  :b1  etc.
_BATCH_SUFFIX_RE = re.compile(r"(::[A-Z]+-\d+|[-_:][Bb]\d+)\s*$")


def occupied(entry: Entry):
    return [(entry.day, period) for period in range(entry.period, entry.period + entry.length)]


def parent_group(cohort: str) -> str:
    """Return the base academic group, stripping any automatic batch suffix.

    Handles both naming conventions:
      - ``::LAB-1``  / ``::TUTORIAL-2``  (produced by read_data in main.py)
      - ``-B1`` / ``-B2`` / ``_b3``      (used in sample_data.py & legacy data)
    """
    return _BATCH_SUFFIX_RE.sub("", cohort).strip()


def is_batch_cohort(cohort: str) -> bool:
    """True when the cohort string represents a sub-batch, not the whole class."""
    return bool(_BATCH_SUFFIX_RE.search(cohort))


def group_conflict(first: Entry, second: Entry) -> bool:
    """Return True when the two entries cannot be scheduled at the same time.

    Rules:
    - Different base cohorts → no conflict (always safe).
    - Same base cohort, both are sub-batches → no conflict (parallel labs/tutorials allowed).
    - Same base cohort, at least one is the whole class → conflict (all students are present).
    - Same base cohort, same sub-batch → conflict (same students).
    """
    if parent_group(first.cohort) != parent_group(second.cohort):
        return False
    first_is_batch = is_batch_cohort(first.cohort)
    second_is_batch = is_batch_cohort(second.cohort)
    # Both are distinct sub-batches → allowed to run in parallel
    if first_is_batch and second_is_batch and first.cohort != second.cohort:
        return False
    return True


def validate(entries, requirements, rooms, instructors):
    req_by_id = {r.id: r for r in requirements}
    room_by_id = {r.id: r for r in rooms}
    teacher_by_id = {i.id: i for i in instructors}
    errors = []
    seen = defaultdict(list)
    hours = defaultdict(int)

    for entry in entries:
        req = req_by_id.get(entry.requirement_id)
        room = room_by_id.get(entry.room)
        if not req or not room:
            errors.append(f"Unknown requirement or room in {entry.requirement_id}")
            continue
        if entry.length != req.block_size:
            errors.append(f"H1: {entry.course} has wrong block length")
        if entry.day not in DAYS or entry.period not in PERIODS or entry.period + entry.length - 1 > 8:
            errors.append(f"H8: {entry.course} is outside the time grid")
        if any(p in BREAKS for _, p in occupied(entry)):
            errors.append(f"H7: {entry.course} crosses the lunch break")
        if room.room_type != req.room_type:
            errors.append(f"H5: {entry.course} needs {req.room_type}")
        if room.capacity < req.students:
            errors.append(f"H6: {entry.course} exceeds room capacity")
        if req.accessible_room and not room.accessible:
            errors.append(f"H5: {entry.course} needs an accessible room")
        teacher = teacher_by_id.get(entry.instructor)
        if teacher and any(f"{day}-{period}" in teacher.unavailable for day, period in occupied(entry)):
            errors.append(f"H8: {teacher.name} is unavailable")
        for day, period in occupied(entry):
            for key in (("room", entry.room), ("teacher", entry.instructor)):
                seen[(key, day, period)].append(entry.course)
        hours[entry.instructor] += entry.length
    # Group conflict is special: a whole-class lecture conflicts with every batch,
    # but Lab Group 1 and Lab Group 2 are allowed to run in parallel.
    for index, first in enumerate(entries):
        for second in entries[index + 1:]:
            if group_conflict(first, second) and set(occupied(first)).intersection(occupied(second)):
                errors.append(f"H2: academic group conflict between {first.course} and {second.course}")

    for (resource, day, period), courses in seen.items():
        if len(courses) > 1:
            code = {"room": "H4", "teacher": "H3", "cohort": "H2"}[resource[0]]
            errors.append(f"{code}: {resource[0]} conflict on {day} P{period}: {', '.join(courses)}")
    for instructor_id, total in hours.items():
        person = teacher_by_id.get(instructor_id)
        if person and total > person.max_hours_week:
            errors.append(f"H9: {person.name} exceeds weekly load")
    for req in requirements:
        actual = sum(e.length for e in entries if e.requirement_id == req.id)
        if actual != req.hours:
            errors.append(f"H1: {req.course} needs {req.hours} hours but has {actual}")
    return errors
