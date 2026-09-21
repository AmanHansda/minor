"""Small JSON persistence layer for the departmental pilot.

Replace this module with PostgreSQL repositories when deploying for multiple
departments and authenticated users.
"""
import json
from pathlib import Path
from .solver.models import Room, Instructor, Requirement


def save_input(path: Path, requirements, rooms, instructors, class_groups=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"requirements": [x.__dict__ for x in requirements], "rooms": [x.__dict__ for x in rooms], "instructors": [x.__dict__ for x in instructors], "class_groups": class_groups or []}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_input(path: Path):
    if not path.exists():
        return None
    body = json.loads(path.read_text(encoding="utf-8"))
    rooms = [Room(**x) for x in body["rooms"]]
    instructors = [Instructor(**x) for x in body["instructors"]]
    requirements = [Requirement(**x) for x in body["requirements"]]
    return requirements, rooms, instructors, body.get("class_groups", [])
