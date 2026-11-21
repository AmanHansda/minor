from .solver.models import Room, Instructor, Requirement


def load_demo():
    rooms = [
        Room("LH1", "A Block Lecture Hall", "LECTURE", 120, "A", True, "CSE"),
        Room("CR1", "A Block Classroom", "CLASSROOM", 65, "A", True, "CSE"),
        Room("LAB1", "Computer Lab 1", "LAB", 32, "A", True, "CSE"),
        Room("LAB2", "Computer Lab 2", "LAB", 32, "A", True, "CSE"),
        Room("PHY1", "Physics Lab", "LAB", 32, "C", True, "Physics"),
    ]
    instructors = [
        Instructor("I1", "Dr. Sharma", preferred=["Mon-1", "Tue-1"]),
        Instructor("I2", "Prof. Verma"),
        Instructor("I3", "Ms. Khan", unavailable=["Mon-1", "Mon-2", "Wed-1", "Wed-2"]),
        Instructor("I4", "Lab Instructor"),
    ]
    reqs = [
        Requirement("R1", "Data Structures", "CSE-S3-A", "I1", 60, 3, 1, "LECTURE", allocation_type="CLASS"),
        Requirement("R2", "Data Structures Lab [LAB Group 1]", "CSE-S3-A::LAB-1", "I4", 30, 2, 2, "LAB", allocation_type="LAB"),
        Requirement("R3", "Data Structures Lab [LAB Group 2]", "CSE-S3-A::LAB-2", "I4", 30, 2, 2, "LAB", allocation_type="LAB"),
        Requirement("R4", "Discrete Mathematics", "CSE-S3-A", "I2", 60, 3, 1, "LECTURE", allocation_type="CLASS"),
        Requirement("R5", "Database Systems", "CSE-S3-A", "I3", 60, 3, 1, "CLASSROOM", allocation_type="CLASS"),
        Requirement("R6", "Database Lab [LAB Group 1]", "CSE-S3-A::LAB-1", "I3", 30, 2, 2, "LAB", allocation_type="LAB"),
    ]
    return reqs, rooms, instructors


def load_demo_groups():
    return [
        {"code": "CSE-S3-A", "program": "B.Tech", "year": "3rd Year", "section": "A", "students": 60, "department": "CSE"}
    ]
