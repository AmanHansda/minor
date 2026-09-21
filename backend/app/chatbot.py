"""Rule-based, read-only timetable help chat. No AI service or network call is used."""
from collections import defaultdict


def answer(message, entries, instructors, rooms):
    if not entries:
        return "Please generate the timetable first, then I can answer timetable questions."
    text = message.lower().strip()
    if any(word in text for word in ("help", "what can", "question")):
        return "Ask things like: 'show CSE S3 A timetable', 'where is Data Structures', 'Dr Sharma schedule', or 'is LAB1 free on Monday period 2?'."
    for entry in entries:
        if entry.course.lower() in text:
            return f"{entry.course} for {entry.cohort} is on {entry.day}, period {entry.period}, in {entry.room}, for {entry.length} hour(s)."
        if entry.cohort.lower().replace("-", " ") in text.replace("-", " "):
            group = sorted([e for e in entries if e.cohort == entry.cohort], key=lambda e: (e.day, e.period))
            return f"{entry.cohort}: " + "; ".join(f"{e.course} - {e.day} P{e.period}, {e.room}" for e in group)
    for person in instructors:
        last = person.name.lower().split()[-1]
        if last in text:
            sessions = [e for e in entries if e.instructor == person.id]
            if not sessions:
                return f"{person.name} has no classes in the current timetable."
            return f"{person.name}: " + "; ".join(f"{e.course} on {e.day} P{e.period} in {e.room}" for e in sessions)
    if "free" in text or "available" in text:
        for room in rooms:
            if room.id.lower() in text or room.name.lower() in text:
                used = ", ".join(f"{e.day} P{e.period}" for e in entries if e.room == room.id) or "no scheduled slots"
                return f"{room.name} ({room.id}) is used at: {used}. Other listed periods are free in this weekly timetable."
        return "Please include a room code, for example: 'Is LAB1 free?'."
    return "I could not match that to the timetable. Try 'help' to see supported questions."
