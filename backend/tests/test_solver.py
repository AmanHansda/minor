import unittest
from backend.app.sample_data import load_demo
from backend.app.solver.engine import generate
from backend.app.solver.models import Entry
from backend.app.solver.validator import validate, occupied
from backend.app.services import (
    quality_report,
    export_class_csv,
    export_teacher_csv,
    export_room_csv,
)
from backend.app.chatbot import answer
from backend.app.main import read_data


class SolverTests(unittest.TestCase):
    def setUp(self):
        self.requirements, self.rooms, self.instructors = load_demo()

    def test_demo_solves_without_violations(self):
        schedule = generate(self.requirements, self.rooms, self.instructors)
        self.assertEqual(schedule.status, "FEASIBLE", schedule.messages)
        self.assertEqual(validate(schedule.entries, self.requirements, self.rooms, self.instructors), [])

    def test_validator_detects_room_conflict(self):
        e1 = Entry("R1", "Data Structures", "A", "I1", "LH1", "Mon", 1, 1)
        e2 = Entry("R4", "Discrete Mathematics", "B", "I2", "LH1", "Mon", 1, 1)
        errors = validate([e1, e2], self.requirements, self.rooms, self.instructors)
        self.assertTrue(any("H4" in err for err in errors))

    def test_quality_has_required_indicators(self):
        schedule = generate(self.requirements, self.rooms, self.instructors)
        report = quality_report(schedule.entries, self.requirements, self.rooms, self.instructors)
        self.assertIn("resilience_score", report)
        self.assertIn("preference_score", report)
        self.assertEqual(report["hard_violations"], 0)

    def test_chat_answers_course_question(self):
        schedule = generate(self.requirements, self.rooms, self.instructors)
        response = answer("where is data structures", schedule.entries, self.instructors, self.rooms)
        self.assertIn("Data Structures", response)

    def test_input_payload_is_converted_to_domain_data(self):
        body = {
            "rooms": [{"id": "A1", "room_type": "CLASSROOM", "capacity": 60}],
            "instructors": [{"id": "T1", "name": "Dr Rao", "preferred": ["Mon-1", "Tue-2"]}],
            "requirements": [
                {
                    "id": "C1",
                    "course": "Algorithms",
                    "cohort": "CSE-5-A",
                    "instructor": "T1",
                    "students": 55,
                    "hours": 3,
                    "block_size": 1,
                    "room_type": "CLASSROOM",
                }
            ],
        }
        requirements, rooms, people = read_data(body)
        self.assertEqual((requirements[0].course, rooms[0].capacity, people[0].name), ("Algorithms", 60, "Dr Rao"))
        self.assertEqual(people[0].preferred, ["Mon-1", "Tue-2"])

    def test_tutorial_and_lab_are_expanded_into_groups(self):
        body = {
            "rooms": [{"id": "L1", "room_type": "LAB", "capacity": 30}, {"id": "C1", "room_type": "CLASSROOM", "capacity": 25}],
            "instructors": [{"id": "T1", "name": "Dr Rao", "max_hours_week": 30}],
            "requirements": [
                {
                    "id": "LAB",
                    "course": "Programming Lab",
                    "cohort": "CSE-BTech-1stYear",
                    "instructor": "T1",
                    "students": 60,
                    "hours": 2,
                    "allocation_type": "LAB",
                },
                {
                    "id": "TUT",
                    "course": "Mathematics Tutorial",
                    "cohort": "CSE-BTech-1stYear",
                    "instructor": "T1",
                    "students": 60,
                    "hours": 1,
                    "allocation_type": "TUTORIAL",
                },
            ],
        }
        requirements, _, _ = read_data(body)
        self.assertEqual(len(requirements), 5)
        self.assertEqual({x.students for x in requirements if "LAB" in x.id}, {30})
        self.assertEqual({x.students for x in requirements if "TUT" in x.id}, {20})

    def test_full_class_conflicts_with_lab_batch_but_distinct_batches_can_overlap(self):
        lecture = Entry("R1", "Lecture", "CSE-BTech-1stYear", "I1", "LH1", "Mon", 1, 1)
        lab_one = Entry("R2", "Lab One", "CSE-BTech-1stYear::LAB-1", "I2", "LAB1", "Mon", 1, 1)
        lab_two = Entry("R3", "Lab Two", "CSE-BTech-1stYear::LAB-2", "I3", "LAB2", "Mon", 1, 1)
        from backend.app.solver.validator import group_conflict

        self.assertTrue(group_conflict(lecture, lab_one))
        self.assertFalse(group_conflict(lab_one, lab_two))

    def test_per_entity_exports(self):
        schedule = generate(self.requirements, self.rooms, self.instructors)
        class_csv = export_class_csv(schedule.entries, "CSE-S3-A")
        self.assertIn("Data Structures", class_csv)
        teacher_csv = export_teacher_csv(schedule.entries, "I1")
        self.assertIn("I1", teacher_csv)
        room_csv = export_room_csv(schedule.entries, "LH1")
        self.assertIn("LH1", room_csv)

    def test_generated_schedule_never_has_room_overlap(self):
        schedule = generate(self.requirements, self.rooms, self.instructors)
        by_room = {}
        for entry in schedule.entries:
            for day, period in occupied(entry):
                key = (entry.room, day, period)
                self.assertNotIn(key, by_room, f"Room double-booking found: {key}")
                by_room[key] = entry.course


if __name__ == "__main__":
    unittest.main()
