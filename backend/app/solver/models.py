from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Room:
    id: str
    name: str
    room_type: str
    capacity: int
    building: str
    accessible: bool = True
    department: str = "General"


@dataclass
class Instructor:
    id: str
    name: str
    max_hours_week: int = 18
    unavailable: List[str] = field(default_factory=list)
    preferred: List[str] = field(default_factory=list)


@dataclass
class Requirement:
    id: str
    course: str
    cohort: str
    instructor: str
    students: int
    hours: int
    block_size: int
    room_type: str
    accessible_room: bool = False
    locked_slot: Optional[str] = None


@dataclass
class Entry:
    requirement_id: str
    course: str
    cohort: str
    instructor: str
    room: str
    day: str
    period: int
    length: int

    @property
    def slot(self) -> str:
        return f"{self.day}-{self.period}"


@dataclass
class Schedule:
    entries: List[Entry]
    status: str = "FEASIBLE"
    messages: List[str] = field(default_factory=list)
