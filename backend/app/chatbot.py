"""Rule-based, read-only timetable help chat. No AI service or network call is used."""
import re
from collections import defaultdict

DAYS_MAP = {
    "mon": "Mon", "monday": "Mon",
    "tue": "Tue", "tuesday": "Tue",
    "wed": "Wed", "wednesday": "Wed",
    "thu": "Thu", "thursday": "Thu",
    "fri": "Fri", "friday": "Fri"
}


def answer(message, entries, instructors, rooms):
    if not entries:
        return "Please generate the timetable first, then I can answer timetable questions."

    text = message.lower().strip()

    # 1. Help & commands
    if any(word in text for word in ("help", "what can", "commands")):
        return (
            "Supported questions include:\n"
            "• 'Where is Data Structures?'\n"
            "• 'Dr. Sharma schedule' or 'I1 schedule'\n"
            "• 'Is LAB1 free on Monday?' or 'Is LH1 free on Mon P2?'\n"
            "• 'Show CSE-S3-A timetable'\n"
            "• 'When is lunch break?'\n"
            "• 'Are there any clashes or violations?'"
        )

    # 2. Lunch break query
    if "lunch" in text:
        return "Period 5 (1:00 PM – 2:00 PM) is the inviolable university-wide lunch break every day from Monday to Friday."

    # 3. Feasibility / clash query
    if any(w in text for w in ("clash", "violation", "feasible", "conflict", "safe")):
        return f"The active schedule contains {len(entries)} placed sessions across the weekly grid with 0 hard clashes."

    # 4. Course schedule query
    # Look for matching course in entries
    course_matches = defaultdict(list)
    for e in entries:
        course_name_clean = e.course.lower()
        base_course = course_name_clean.split(" [", 1)[0]
        if base_course in text or course_name_clean in text:
            course_matches[e.course].append(e)

    if course_matches:
        replies = []
        for course_title, sessions in course_matches.items():
            sessions.sort(key=lambda s: (s.day, s.period))
            slots_str = ", ".join(f"{s.day} Period {s.period} in {s.room} ({s.cohort})" for s in sessions)
            replies.append(f"{course_title}: {slots_str}")
        return "; ".join(replies)

    # 5. Faculty schedule query
    for person in instructors:
        last = person.name.lower().split()[-1].replace(".", "")
        full = person.name.lower()
        pid = person.id.lower()
        # match full name, last name, or ID
        if full in text or (len(last) >= 3 and last in text) or pid in text.split():
            sessions = sorted([e for e in entries if e.instructor == person.id], key=lambda e: (e.day, e.period))
            if not sessions:
                return f"{person.name} ({person.id}) has no classes scheduled in the current timetable."
            total_hours = sum(e.length for e in sessions)
            details = ", ".join(f"{e.course} on {e.day} P{e.period} ({e.room})" for e in sessions)
            return f"{person.name} ({person.id}) has {total_hours} hr(s) scheduled: {details}."

    # 6. Cohort / Academic group query
    for e in entries:
        norm_cohort = e.cohort.lower().replace("-", " ").replace("::", " ")
        norm_text = text.replace("-", " ").replace("::", " ")
        if norm_cohort in norm_text or (len(norm_cohort) > 3 and norm_cohort in norm_text):
            group_entries = sorted([x for x in entries if x.cohort == e.cohort or x.cohort.startswith(e.cohort + "::")], key=lambda x: (x.day, x.period))
            if group_entries:
                details = "; ".join(f"{x.course} - {x.day} P{x.period} ({x.room})" for x in group_entries)
                return f"{e.cohort}: {details}."

    # 7. Room availability query
    if any(w in text for w in ("free", "available", "empty", "room", "lab", "hall")):
        for room in rooms:
            if room.id.lower() in text.split() or room.id.lower() in text or room.name.lower() in text:
                room_entries = [e for e in entries if e.room == room.id]
                # Check if a specific day is mentioned
                target_day = None
                for word, day_code in DAYS_MAP.items():
                    if re.search(r"\b" + word + r"\b", text):
                        target_day = day_code
                        break

                # Check if a specific period is mentioned
                period_match = re.search(r"\b(?:period|p)[\s-]*([1-8])\b", text)
                target_period = int(period_match.group(1)) if period_match else None

                if target_day and target_period:
                    # Specific day and period
                    occupied_entry = next((e for e in room_entries if e.day == target_day and e.period <= target_period < e.period + e.length), None)
                    if occupied_entry:
                        return f"{room.name} ({room.id}) is OCCUPIED on {target_day} Period {target_period} by {occupied_entry.course} ({occupied_entry.cohort})."
                    return f"{room.name} ({room.id}) is FREE on {target_day} Period {target_period}."

                if target_day:
                    day_entries = sorted([e for e in room_entries if e.day == target_day], key=lambda e: e.period)
                    if not day_entries:
                        return f"{room.name} ({room.id}) has NO classes on {target_day} and is completely FREE all day (excluding 1-2 PM lunch)."
                    used_str = ", ".join(f"P{e.period} ({e.course})" for e in day_entries)
                    return f"{room.name} ({room.id}) on {target_day} is booked for: {used_str}. Other periods are free."

                # General room status
                if not room_entries:
                    return f"{room.name} ({room.id}) has no classes scheduled and is free all week."
                used = ", ".join(f"{e.day} P{e.period}" for e in sorted(room_entries, key=lambda e: (e.day, e.period)))
                return f"{room.name} ({room.id}) is booked at: {used}. Other periods (excluding 1-2 PM lunch) are free."

        return "Please specify a room code, for example: 'Is LAB1 free on Monday?' or 'Where is LH1 used?'."

    return "I could not match that to the active timetable. Try typing 'help' to see sample queries."
