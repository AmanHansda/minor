"""Create a feasible whole-department timetable import workbook."""
from pathlib import Path

from backend.app import xlsx_io


PROGRAMMES = [
    ("B.Tech", "1st Year", "S1", 60, ("A", "B")),
    ("B.Tech", "2nd Year", "S3", 60, ("A", "B")),
    ("B.Tech", "3rd Year", "S5", 60, ("A", "B")),
    ("B.Tech", "4th Year", "S7", 60, ("A", "B")),
    ("M.Tech", "1st Year", "M1", 30, ("A",)),
    ("M.Tech", "2nd Year", "M3", 30, ("A",)),
    ("PhD", "1st Year", "P1", 12, ("A",)),
    ("PhD", "2nd Year", "P2", 12, ("A",)),
]

SUBJECTS = {
    "S1": [("CS101", "Programming Fundamentals", "CLASS", 3, 1), ("MA101", "Engineering Mathematics", "TUTORIAL", 1, 1), ("CS102", "Programming Laboratory", "LAB", 2, 2), ("HS101", "Communication Skills", "CLASS", 2, 1)],
    "S3": [("CS201", "Data Structures", "CLASS", 3, 1), ("MA201", "Discrete Mathematics Tutorial", "TUTORIAL", 1, 1), ("CS202", "Data Structures Laboratory", "LAB", 2, 2), ("CS203", "Computer Organization", "CLASS", 2, 1)],
    "S5": [("CS301", "Operating Systems", "CLASS", 3, 1), ("CS302", "Database Systems Tutorial", "TUTORIAL", 1, 1), ("CS303", "Database Laboratory", "LAB", 2, 2), ("CS304", "Computer Networks", "CLASS", 2, 1)],
    "S7": [("CS401", "Machine Learning", "CLASS", 3, 1), ("CS402", "Cloud Computing Tutorial", "TUTORIAL", 1, 1), ("CS403", "Machine Learning Laboratory", "LAB", 2, 2), ("CS404", "Software Engineering", "CLASS", 2, 1)],
    "M1": [("MC501", "Advanced Algorithms", "CLASS", 3, 1), ("MC502", "Research Methods Tutorial", "TUTORIAL", 1, 1), ("MC503", "Advanced Computing Laboratory", "LAB", 2, 2), ("MC504", "Distributed Systems", "CLASS", 2, 1)],
    "M3": [("MC601", "Thesis Seminar", "CLASS", 2, 1), ("MC602", "Cloud Architecture Tutorial", "TUTORIAL", 1, 1), ("MC603", "Research Laboratory", "LAB", 2, 2), ("MC604", "Industry Project", "CLASS", 2, 1)],
    "P1": [("PC701", "Doctoral Seminar", "CLASS", 2, 1), ("PC702", "Research Design Tutorial", "TUTORIAL", 1, 1), ("PC703", "Research Computing Laboratory", "LAB", 2, 2), ("PC704", "Literature Review", "CLASS", 2, 1)],
    "P2": [("PC801", "Thesis Colloquium", "CLASS", 2, 1), ("PC802", "Publication Workshop Tutorial", "TUTORIAL", 1, 1), ("PC803", "Advanced Research Laboratory", "LAB", 2, 2), ("PC804", "Dissertation Review", "CLASS", 2, 1)],
}


def build_dataset():
    groups, rooms, faculty, allocations = [], [], [], []
    for programme, year, semester, strength, sections in PROGRAMMES:
        for section in sections:
            groups.append([f"CSE-{semester}-{section}", "CSE", programme, year, section, strength])

    rooms.extend([[f"LH{i}", f"Lecture Hall {i}", "LECTURE", 90, "Academic Block", "CSE", "TRUE"] for i in range(1, 7)])
    rooms.extend([[f"CR{i}", f"Tutorial Room {i}", "CLASSROOM", 35, "Academic Block", "CSE", "TRUE"] for i in range(1, 9)])
    rooms.extend([[f"LAB{i}", f"Computing Laboratory {i}", "LAB", 36, "Lab Block", "CSE", "TRUE"] for i in range(1, 9)])

    faculty.extend([
        ["F-B1-A", "Dr. Aditi Verma", 24, "", "Mon-1, Tue-2"], ["F-B1-B", "Dr. Bala Menon", 24, "", "Mon-1, Tue-2"],
        ["F-B2-A", "Dr. Bharat Mehta", 24, "", "Mon-1, Tue-2"], ["F-B2-B", "Dr. Charu Nair", 24, "", "Mon-1, Tue-2"],
        ["F-B3-A", "Dr. Deepak Iyer", 24, "", "Mon-1, Tue-2"], ["F-B3-B", "Dr. Esha Kulkarni", 24, "", "Mon-1, Tue-2"],
        ["F-B4-A", "Dr. Farhan Ali", 24, "", "Mon-1, Tue-2"], ["F-B4-B", "Dr. Gauri Shah", 24, "", "Mon-1, Tue-2"],
        ["F-M1", "Prof. Harish Rao", 24, "", "Mon-1, Tue-2"], ["F-M2", "Prof. Indira Bose", 24, "", "Mon-1, Tue-2"],
        ["F-M3", "Prof. Jatin Sethi", 24, "", "Mon-1, Tue-2"], ["F-M4", "Prof. Kavita Das", 24, "", "Mon-1, Tue-2"],
        ["F-P1", "Dr. Leela Raman", 24, "", "Mon-1, Tue-2"], ["F-P2", "Dr. Mohan Pillai", 24, "", "Mon-1, Tue-2"],
        ["F-P3", "Dr. Nisha Gupta", 24, "", "Mon-1, Tue-2"], ["F-P4", "Dr. Omar Khan", 24, "", "Mon-1, Tue-2"],
    ])

    # Each faculty member teaches multiple related subjects. B.Tech faculty
    # cover both sections of a year; M.Tech and PhD faculty span both years.
    teacher_by_subject = {
        "S1": ("F-B1-A", "F-B1-B", "F-B1-B", "F-B1-A"),
        "S3": ("F-B2-A", "F-B2-B", "F-B2-B", "F-B2-A"),
        "S5": ("F-B3-A", "F-B3-B", "F-B3-B", "F-B3-A"),
        "S7": ("F-B4-A", "F-B4-B", "F-B4-B", "F-B4-A"),
        "M1": ("F-M1", "F-M2", "F-M3", "F-M4"),
        "M3": ("F-M2", "F-M3", "F-M4", "F-M1"),
        "P1": ("F-P1", "F-P2", "F-P3", "F-P4"),
        "P2": ("F-P2", "F-P3", "F-P4", "F-P1"),
    }

    for programme, year, semester, strength, sections in PROGRAMMES:
        for section in sections:
            cohort = f"CSE-{semester}-{section}"
            for subject_number, (code, name, allocation_type, hours, block_size) in enumerate(SUBJECTS[semester], 1):
                teacher_id = teacher_by_subject[semester][subject_number - 1]
                allocations.append([code, name, cohort, teacher_id, allocation_type, hours, block_size, "FALSE"])
    return groups, rooms, faculty, allocations


if __name__ == "__main__":
    groups, rooms, faculty, allocations = build_dataset()
    xlsx_io.SAMPLES.update({"Groups": groups, "Rooms": rooms, "Faculty": faculty, "Allocations": allocations, "Configuration": [["13:00"]]})
    target = Path("outputs/whole_department_timetable_dataset/chronosai_whole_department_dataset.xlsx")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(xlsx_io.build_template())
    data = xlsx_io.parse_upload(target.read_bytes())
    assert len(data["class_groups"]) == 12
    assert len(data["instructors"]) == 16
    assert len(data["requirements"]) == 48
    assert {item["allocation_type"] for item in data["requirements"]} == {"CLASS", "TUTORIAL", "LAB"}
    print(target.resolve())
    print(f"Validated {len(groups)} groups, {len(rooms)} rooms, {len(faculty)} faculty, {len(allocations)} allocations")
