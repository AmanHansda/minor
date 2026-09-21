"""A transparent deterministic heuristic. Swap with OR-Tools in a future iteration."""
from .models import Entry, Schedule
from .validator import DAYS, PERIODS, BREAKS, validate, occupied, group_conflict


def _candidate_slots(req):
    if req.locked_slot:
        day, period = req.locked_slot.split("-")
        return [(day, int(period))]
    return [(day, p) for day in DAYS for p in PERIODS if p + req.block_size - 1 <= 8 and not any(x in BREAKS for x in range(p, p + req.block_size))]


def generate(requirements, rooms, instructors, locked=None):
    """Place most constrained requirements first; each meeting is a separate entry."""
    entries = list(locked or [])
    messages = []
    teacher_by_id = {i.id: i for i in instructors}

    def can_place(candidate):
        """Partial feasibility check; full hour totals are checked after generation."""
        teacher = teacher_by_id.get(candidate.instructor)
        if teacher and any(f"{day}-{period}" in teacher.unavailable for day, period in occupied(candidate)):
            return False
        for existing in entries:
            # Spread repeated meetings of the same course/group across the week.
            candidate_course = candidate.course.split(" [", 1)[0]
            existing_course = existing.course.split(" [", 1)[0]
            if candidate.day == existing.day and candidate_course == existing_course and candidate.cohort == existing.cohort:
                return False
            if not set(occupied(candidate)).intersection(occupied(existing)):
                continue
            if candidate.room == existing.room or candidate.instructor == existing.instructor or group_conflict(candidate, existing):
                return False
        current_hours = sum(e.length for e in entries if e.instructor == candidate.instructor)
        return not teacher or current_hours + candidate.length <= teacher.max_hours_week
    ordered = sorted(requirements, key=lambda r: (len([x for x in rooms if x.room_type == r.room_type and x.capacity >= r.students]), -r.block_size, -r.hours))
    for req in ordered:
        remaining = req.hours
        while remaining:
            placed = False
            for day, period in _candidate_slots(req):
                for room in rooms:
                    if room.room_type != req.room_type or room.capacity < req.students or (req.accessible_room and not room.accessible):
                        continue
                    candidate = Entry(req.id, req.course, req.cohort, req.instructor, room.id, day, period, req.block_size)
                    if can_place(candidate):
                        entries.append(candidate)
                        placed = True
                        break
                if placed:
                    break
            if not placed:
                messages.append(f"Could not place {req.course} for {req.cohort}. Check rooms, availability or required hours.")
                break
            remaining -= req.block_size
    errors = validate(entries, requirements, rooms, instructors)
    return Schedule(entries, "FEASIBLE" if not errors else "INFEASIBLE", messages + errors)
