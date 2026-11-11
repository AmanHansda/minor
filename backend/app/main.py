"""Small standard-library HTTP server for the ChronosAI demonstrator."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import re
import urllib.parse
from .sample_data import load_demo, load_demo_groups
from .solver.engine import generate
from .services import (
    quality_report,
    explain_slot,
    absent_reschedule,
    export_csv,
    export_ical,
    export_class_csv,
    export_teacher_csv,
    export_room_csv,
)
from .chatbot import answer
from .solver.models import Room, Instructor, Requirement
from .storage import save_input, load_input

ROOT = Path(__file__).resolve().parents[2]
STATE = {"schedule": None, "data": None, "class_groups": []}
INPUT_FILE = ROOT / "data" / "department_input.json"
def current_data():
    if STATE["data"]:
        return STATE["data"]
    saved = load_input(INPUT_FILE)
    if saved:
        requirements, rooms, people, groups = saved
        STATE["class_groups"] = groups
        return requirements, rooms, people
    reqs, rooms, people = load_demo()
    STATE["class_groups"] = load_demo_groups()
    return reqs, rooms, people


def read_data(body):
    """Convert safe JSON form data into the internal scheduling objects."""
    rooms = [
        Room(
            str(x["id"]),
            str(x.get("name") or x["id"]),
            str(x["room_type"]),
            int(x["capacity"]),
            str(x.get("building", "Main")),
            bool(x.get("accessible", True)),
            str(x.get("department", "General")),
        )
        for x in body.get("rooms", [])
    ]
    people = [
        Instructor(
            str(x["id"]),
            str(x["name"]),
            int(x.get("max_hours_week", 18)),
            list(x.get("unavailable", [])),
            list(x.get("preferred", [])),
        )
        for x in body.get("instructors", [])
    ]
    requirements = []
    seen_allocations = set()
    for item in body.get("requirements", []):
        alloc_type = str(item.get("allocation_type", "")).upper()
        if not alloc_type:
            rt = str(item.get("room_type", "")).upper()
            if rt == "LAB" or "lab" in str(item.get("course", "")).lower():
                alloc_type = "LAB"
            elif rt == "CLASSROOM" or "tutorial" in str(item.get("course", "")).lower():
                alloc_type = "TUTORIAL" if "tutorial" in str(item.get("course", "")).lower() else "CLASS"
            else:
                alloc_type = "CLASS"

        is_batch = (
            "::" in str(item.get("cohort", ""))
            or " [" in str(item.get("course", ""))
            or bool(re.search(r"[-_:]b\d+", str(item.get("cohort", "")), re.IGNORECASE) and alloc_type == "LAB")
        )

        if is_batch:
            groups = 1
            room_type = str(item.get("room_type") or ("LAB" if alloc_type == "LAB" else ("CLASSROOM" if alloc_type == "TUTORIAL" else "LECTURE")))
        else:
            groups, default_rt = {"CLASS": (1, "LECTURE"), "TUTORIAL": (3, "CLASSROOM"), "LAB": (2, "LAB")}.get(
                alloc_type, (1, "LECTURE")
            )
            room_type = str(item.get("room_type") or default_rt)

        block_size = int(item.get("block_size", 2 if alloc_type == "LAB" else 1))
        course_str = str(item["course"])
        cohort_str = str(item["cohort"])
        identity = (course_str.strip().lower(), cohort_str.strip().lower(), alloc_type)
        if identity in seen_allocations:
            raise ValueError("A subject may have only one allocation of each type for an academic group.")
        seen_allocations.add(identity)

        for number in range(1, groups + 1):
            suffix = "" if groups == 1 else f" [{alloc_type} Group {number}]"
            cohort = cohort_str if groups == 1 else f"{cohort_str}::{alloc_type}-{number}"
            req_id = f"{item['id']}-{number}" if groups > 1 else str(item["id"])
            requirements.append(
                Requirement(
                    req_id,
                    course_str + suffix,
                    cohort,
                    str(item["instructor"]),
                    -(-int(item["students"]) // groups),
                    int(item["hours"]),
                    block_size,
                    room_type,
                    bool(item.get("accessible_room", False)),
                    allocation_type=alloc_type,
                )
            )
    if not rooms or not people or not requirements:
        raise ValueError("Add at least one classroom, teacher and class requirement.")
    instructor_ids = {x.id for x in people}
    if any(x.instructor not in instructor_ids for x in requirements):
        raise ValueError("Every class requirement must be linked to a teacher.")
    return requirements, rooms, people


class Handler(SimpleHTTPRequestHandler):
    def _send_json(self, value, status=200):
        raw = json.dumps(value, default=lambda x: x.__dict__).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        if path == "/api/health":
            return self._send_json({"status": "ok", "project": "ChronosAI"})

        if path == "/api/demo":
            if query.get("reset", ["0"])[0] in ("1", "true"):
                STATE["data"] = None
                STATE["schedule"] = None
                demo_reqs, demo_rooms, demo_people = load_demo()
                demo_groups = load_demo_groups()
                STATE["class_groups"] = demo_groups
                save_input(INPUT_FILE, demo_reqs, demo_rooms, demo_people, demo_groups)
                return self._send_json(
                    {"requirements": demo_reqs, "rooms": demo_rooms, "instructors": demo_people, "class_groups": demo_groups}
                )
            reqs, rooms, people = current_data()
            groups = STATE["class_groups"] or load_demo_groups()
            return self._send_json(
                {"requirements": reqs, "rooms": rooms, "instructors": people, "class_groups": groups}
            )

        if path == "/api/data":
            reqs, rooms, people = current_data()
            groups = STATE["class_groups"] or load_demo_groups()
            return self._send_json(
                {"requirements": reqs, "rooms": rooms, "instructors": people, "class_groups": groups}
            )

        reqs, rooms, people = current_data()

        if path == "/api/generate":
            STATE["schedule"] = generate(reqs, rooms, people)
            return self._send_json(
                {
                    "schedule": STATE["schedule"],
                    "quality": quality_report(STATE["schedule"].entries, reqs, rooms, people),
                }
            )
        if path == "/api/export/csv":
            if not STATE["schedule"]:
                return self._send_json({"error": "Generate timetable first"}, 400)
            raw = export_csv(STATE["schedule"].entries).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/csv")
            self.send_header("Content-Disposition", 'attachment; filename="timetable_master.csv"')
            self.end_headers()
            return self.wfile.write(raw)
        if path == "/api/export/ical":
            if not STATE["schedule"]:
                return self._send_json({"error": "Generate timetable first"}, 400)
            raw = export_ical(STATE["schedule"].entries).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/calendar")
            self.send_header("Content-Disposition", 'attachment; filename="timetable.ics"')
            self.end_headers()
            return self.wfile.write(raw)
        if path.startswith("/api/export/class/"):
            if not STATE["schedule"]:
                return self._send_json({"error": "Generate timetable first"}, 400)
            target = urllib.parse.unquote(path[len("/api/export/class/") :])
            raw = export_class_csv(STATE["schedule"].entries, target).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/csv")
            self.send_header("Content-Disposition", f'attachment; filename="class_{target}.csv"')
            self.end_headers()
            return self.wfile.write(raw)
        if path.startswith("/api/export/teacher/"):
            if not STATE["schedule"]:
                return self._send_json({"error": "Generate timetable first"}, 400)
            target = urllib.parse.unquote(path[len("/api/export/teacher/") :])
            raw = export_teacher_csv(STATE["schedule"].entries, target).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/csv")
            self.send_header("Content-Disposition", f'attachment; filename="teacher_{target}.csv"')
            self.end_headers()
            return self.wfile.write(raw)
        if path.startswith("/api/export/room/"):
            if not STATE["schedule"]:
                return self._send_json({"error": "Generate timetable first"}, 400)
            target = urllib.parse.unquote(path[len("/api/export/room/") :])
            raw = export_room_csv(STATE["schedule"].entries, target).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/csv")
            self.send_header("Content-Disposition", f'attachment; filename="room_{target}.csv"')
            self.end_headers()
            return self.wfile.write(raw)
        if path.startswith("/api/explain/"):
            if not STATE["schedule"]:
                return self._send_json({"error": "Generate timetable first"}, 400)
            try:
                idx = int(path.rsplit("/", 1)[-1])
                if 0 <= idx < len(STATE["schedule"].entries):
                    return self._send_json(explain_slot(STATE["schedule"].entries[idx], reqs, rooms, people))
                return self._send_json({"error": "Invalid slot index"}, 400)
            except ValueError:
                return self._send_json({"error": "Invalid index"}, 400)
        if path.startswith("/api/absence/"):
            if not STATE["schedule"]:
                return self._send_json({"error": "Generate timetable first"}, 400)
            ident = path.rsplit("/", 1)[-1]
            result, diff = absent_reschedule(STATE["schedule"], ident, reqs, rooms, people)
            return self._send_json({"schedule": result, "diff": diff})
        if self.path == "/" or self.path == "/index.html":
            self.path = "/frontend/index.html"
        return super().do_GET()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            if self.path == "/api/data":
                STATE["data"] = read_data(body)
                STATE["schedule"] = None
                STATE["class_groups"] = list(body.get("class_groups", []))
                save_input(INPUT_FILE, *STATE["data"], STATE["class_groups"])
                return self._send_json({"message": "Input data saved. Generate the timetable when ready."})
            if self.path == "/api/chat":
                reqs, rooms, people = current_data()
                reply = answer(
                    str(body.get("message", "")),
                    (STATE["schedule"].entries if STATE["schedule"] else []),
                    people,
                    rooms,
                )
                return self._send_json({"reply": reply})
            return self._send_json({"error": "Not found"}, 404)
        except (ValueError, json.JSONDecodeError) as e:
            return self._send_json({"error": str(e) or "Invalid JSON"}, 400)


if __name__ == "__main__":
    import os

    os.chdir(ROOT)
    port = int(os.environ.get("PORT", os.environ.get("CHRONOS_PORT", "8000")))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"Chronos running at http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
