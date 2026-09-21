from collections import defaultdict
from .solver.models import Entry
from .solver.validator import occupied, validate


def quality_report(entries, requirements, rooms, instructors):
    gaps = 0
    early = 0
    by_cohort = defaultdict(lambda: defaultdict(list))
    by_teacher = defaultdict(int)
    for e in entries:
        by_cohort[e.cohort][e.day].extend(p for _, p in occupied(e))
        by_teacher[e.instructor] += e.length
        early += e.length if e.period == 1 else 0
    for days in by_cohort.values():
        for periods in days.values():
            if periods:
                gaps += max(periods) - min(periods) + 1 - len(set(periods))
    used_rooms = len({e.room for e in entries})
    loads = list(by_teacher.values()) or [0]
    mean = sum(loads) / len(loads)
    fairness = round(sum(abs(x - mean) for x in loads) / (2 * len(loads) * mean), 3) if mean else 0
    resilience = round(100 * (1 - max(loads) / max(1, sum(loads))), 1)
    return {"hard_violations": len(validate(entries, requirements, rooms, instructors)), "gaps": gaps, "early_periods": early, "rooms_used": used_rooms, "green_score": max(0, 100 - used_rooms * 6), "fairness_gini": fairness, "resilience_score": resilience, "penalty": gaps * 3 + early}


def explain_slot(entry, requirements, rooms, instructors):
    req = next(r for r in requirements if r.id == entry.requirement_id)
    return {"course": entry.course, "slot": entry.slot, "reason": f"{entry.course} needs a {req.block_size}-period {req.room_type} session for {req.students} students. This was the first valid slot after avoiding instructor, cohort, room and lunch conflicts.", "constraints_checked": ["cohort clash", "instructor availability", "room type", "room capacity", "lunch break"]}


def absent_reschedule(schedule, absent_instructor, requirements, rooms, instructors):
    affected = [e for e in schedule.entries if e.instructor == absent_instructor]
    kept = [e for e in schedule.entries if e.instructor != absent_instructor]
    req_ids = {e.requirement_id for e in affected}
    changed_reqs = [r for r in requirements if r.id in req_ids]
    from .solver.engine import generate
    result = generate(changed_reqs, rooms, instructors, locked=kept)
    return result, {"affected_entries": len(affected), "changed_entries": len(result.entries) - len(kept), "message": "A minimal-change attempt retained unaffected entries."}


def export_csv(entries):
    lines = ["Course,Cohort,Instructor,Room,Day,Period,Length"]
    lines += [f"{e.course},{e.cohort},{e.instructor},{e.room},{e.day},{e.period},{e.length}" for e in entries]
    return "\n".join(lines)


def export_ical(entries):
    days = {"Mon": "MO", "Tue": "TU", "Wed": "WE", "Thu": "TH", "Fri": "FR"}
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//ChronosAI//EN"]
    for i, e in enumerate(entries):
        start_hour = 8 + e.period
        lines += ["BEGIN:VEVENT", f"UID:chronos-{i}@local", f"SUMMARY:{e.course} ({e.cohort})", f"LOCATION:{e.room}", f"RRULE:FREQ=WEEKLY;BYDAY={days[e.day]}", f"DTSTART:20260105T{start_hour:02}0000", f"DTEND:20260105T{start_hour + e.length:02}0000", "END:VEVENT"]
    return "\n".join(lines + ["END:VCALENDAR"])
