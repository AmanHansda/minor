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

    # Soft constraint metric: Instructor preferred slots satisfied
    teacher_by_id = {i.id: i for i in instructors}
    pref_hours_possible = 0
    pref_hours_met = 0
    for e in entries:
        teacher = teacher_by_id.get(e.instructor)
        if teacher and teacher.preferred:
            pref_hours_possible += e.length
            if any(f"{e.day}-{p}" in teacher.preferred for p in range(e.period, e.period + e.length)):
                pref_hours_met += e.length
    preference_score = round(100 * pref_hours_met / max(1, pref_hours_possible), 1) if pref_hours_possible else 100.0

    return {
        "hard_violations": len(validate(entries, requirements, rooms, instructors)),
        "gaps": gaps,
        "early_periods": early,
        "rooms_used": used_rooms,
        "green_score": max(0, 100 - used_rooms * 6),
        "fairness_gini": fairness,
        "resilience_score": resilience,
        "preference_score": preference_score,
        "penalty": gaps * 3 + early
    }


def explain_slot(entry, requirements, rooms, instructors):
    req = next(r for r in requirements if r.id == entry.requirement_id)
    return {
        "course": entry.course,
        "cohort": entry.cohort,
        "instructor": entry.instructor,
        "room": entry.room,
        "day": entry.day,
        "period": entry.period,
        "length": entry.length,
        "slot": entry.slot,
        "reason": f"{entry.course} needs a {req.block_size}-period {req.room_type} session for {req.students} students. This slot was chosen to avoid cohort, instructor and room conflicts while respecting lunch break and availability.",
        "constraints_checked": [
            "cohort clash (H2)",
            "instructor clash & availability (H3, H8)",
            "room clash & type (H4, H5)",
            "room capacity (H6)",
            "lunch break preserved (H7)",
            "faculty weekly workload (H9)"
        ]
    }


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


def export_class_csv(entries, cohort):
    matched = [e for e in entries if e.cohort == cohort or e.cohort.startswith(cohort + "::") or e.cohort.startswith(cohort + "-")]
    lines = ["Course,Academic Group,Instructor,Room,Day,Period,Length"]
    lines += [f'"{e.course}","{e.cohort}","{e.instructor}","{e.room}",{e.day},{e.period},{e.length}' for e in matched]
    return "\n".join(lines)


def export_teacher_csv(entries, instructor_id):
    matched = [e for e in entries if e.instructor == instructor_id]
    lines = ["Course,Academic Group,Instructor,Room,Day,Period,Length"]
    lines += [f'"{e.course}","{e.cohort}","{e.instructor}","{e.room}",{e.day},{e.period},{e.length}' for e in matched]
    return "\n".join(lines)


def export_room_csv(entries, room_id):
    matched = [e for e in entries if e.room == room_id]
    lines = ["Course,Academic Group,Instructor,Room,Day,Period,Length"]
    lines += [f'"{e.course}","{e.cohort}","{e.instructor}","{e.room}",{e.day},{e.period},{e.length}' for e in matched]
    return "\n".join(lines)


def export_ical(entries):
    days = {"Mon": "MO", "Tue": "TU", "Wed": "WE", "Thu": "TH", "Fri": "FR"}
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//ChronosAI//EN"]
    for i, e in enumerate(entries):
        start_hour = 8 + e.period
        lines += ["BEGIN:VEVENT", f"UID:chronos-{i}@local", f"SUMMARY:{e.course} ({e.cohort})", f"LOCATION:{e.room}", f"RRULE:FREQ=WEEKLY;BYDAY={days[e.day]}", f"DTSTART:20260105T{start_hour:02}0000", f"DTEND:20260105T{start_hour + e.length:02}0000", "END:VEVENT"]
    return "\n".join(lines + ["END:VCALENDAR"])
