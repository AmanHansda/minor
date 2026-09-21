"""Single source of truth for timetable safety rules."""
from collections import defaultdict
from .models import Entry, Requirement, Room, Instructor

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
# 9am to 5pm with period 5 (1pm to 2pm) reserved for lunch.
PERIODS = range(1, 9)
BREAKS = {5}


def occupied(entry: Entry):
    return [(entry.day, period) for period in range(entry.period, entry.period + entry.length)]


def parent_group(cohort: str) -> str:
    """Return the academic group before an automatic tutorial/lab batch suffix."""
    return cohort.split("::", 1)[0]


def group_conflict(first: Entry, second: Entry) -> bool:
    """A full class blocks every batch; distinct batches may run in parallel."""
    if parent_group(first.cohort) != parent_group(second.cohort):
        return False
    return "::" not in first.cohort or "::" not in second.cohort or first.cohort == second.cohort


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
