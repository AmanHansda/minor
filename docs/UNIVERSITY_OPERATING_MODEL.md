# Chronos University Operating Model

## Product Position

Chronos is operated by the timetable office. Students and faculty do not create schedules. They receive only the approved group-wise or faculty-wise timetable sheets produced by the timetable office.

The system must balance three legitimate viewpoints:

| Role | What they need | What Chronos guarantees |
|---|---|---|
| Timetable maker | Complete control of academic data, constraints, rooms and publishing | One authoritative version, validation before publishing, traceable changes |
| Student | A clear class timetable, no overlapping compulsory sessions, correct room/time and timely updates | Group sheet, lunch shown, correct faculty and room, only published schedule shared |
| Faculty member | No double booking, known teaching hours, availability respected and a readable teaching sheet | No overlapping allocations, weekly load check, unavailable slots blocked |
| Department/administration | Room utilisation, enough seats, labs used correctly and fair allocation | Capacity/type checks, lab grouping, classroom timetable sheet and quality report |

## Academic Data Workflow

### 1 Academic group setup

Create one academic group for a department, programme and year. Examples:

- CSE B.Tech 1st Year, total strength 120
- CSE B.Tech 3rd Year, total strength 60
- CSE M.Tech 1st Year, total strength 24
- CSE PhD 1st Year, total strength 8

Sections are optional only when the university actually teaches separate sections. They are not created merely to make tutorial or lab batches.

### 2 Faculty setup

For each faculty member record:

- faculty ID and name
- department
- maximum weekly teaching hours
- unavailable time slots, which are hard restrictions
- preferred time slots, which are soft preferences

### 3 Classroom and laboratory setup

For each room record:

- room number/name
- block/building
- allocated department
- type: lecture hall, classroom or lab
- seating capacity
- optional equipment/accessibility information in the production version

### 4 Course allocation setup

For each allocation, enter only:

- course code and course name
- academic group
- faculty teaching it
- contact hours per week
- teaching type

Teaching type determines automatic grouping:

| Teaching type | Students attending | Room type | Grouping |
|---|---|---|---|
| Full Class Lecture | Whole academic group | Lecture hall | One full group |
| Tutorial Class | One third at a time | Classroom | Three automatic tutorial groups |
| Laboratory | One half at a time | Lab | Two automatic lab groups |

Every auto-created tutorial/lab group receives the stated weekly hours. It is normal for a different batch to be free or to be in another laboratory during that time.

## Publishing Pipeline

```text
Draft data
  -> validation of missing/incorrect data
  -> generate timetable
  -> hard-constraint validation
  -> timetable-maker review
  -> faculty workload/availability confirmation
  -> department approval
  -> publish immutable version
  -> share group/faculty/room sheets
  -> controlled revision if necessary
```

The administrator must not publish a schedule if the hard-violation count is not zero.

## Non Negotiable Rules

1. A faculty member cannot teach two meetings in the same time interval.
2. A full academic group cannot have two compulsory meetings in the same interval.
3. A room or laboratory cannot host two meetings in the same interval.
4. A room must have appropriate type and sufficient capacity.
5. Lunch is blocked from 1 PM to 2 PM for all groups, rooms and faculty.
6. A lab uses consecutive periods and must not cross lunch.
7. A course is spread across different weekdays where possible; the same course is not scheduled multiple times on one day.
8. Tutorial and laboratory batches receive equal required weekly hours.
9. Faculty availability and maximum weekly load are hard rules.
10. The system retains the source allocation for every generated timetable entry.

## Required Outputs

The timetable maker produces three official sheets from the same approved schedule:

1. **Academic-group sheet:** a weekly day/time grid, fixed lunch column, course/faculty/room directory and separate batch labels for tutorial/lab groups.
2. **Faculty sheet:** all assigned courses, academic groups, days, exact start/end times, rooms and total weekly contact hours.
3. **Classroom/lab sheet:** all bookings for a selected room, day/time, course, group and faculty. It is used to verify room utilisation and resolve physical-space issues.

## Complaint and Revision Management

No scheduling system can eliminate every preference conflict. Chronos must handle requests fairly:

1. A faculty member or department submits a request with reason and affected allocation.
2. Timetable office labels it: hard conflict, operational issue, or preference.
3. Hard conflicts are corrected before publication.
4. Preferences are assessed against the impact on all academic groups and faculty.
5. A re-generation creates a change list: moved course, old slot, new slot, reason and affected users.
6. Only the timetable office can approve and publish the revision.
7. The new version supersedes the old version; distributed sheets show the version/date.

## Production Acceptance Checklist

Before a university deployment, verify all of the following:

- Import of real faculty, rooms, programmes and academic groups works from approved templates.
- Required entries are present for every offered course.
- Hard-violation count is zero.
- No faculty weekly load exceeds department policy.
- Every tutorial/lab batch has the correct student strength and contact hours.
- Every class has a suitable room and capacity.
- Group, faculty and room sheets agree with each other.
- A printed class sheet clearly shows 1 PM to 2 PM lunch.
- A sample of faculty and student representatives signs off on readability.
- The timetable office can restore a prior approved version.
- Access, data backup, audit history and HTTPS are enabled before public rollout.

## Current Prototype Boundary

The code in this project is a functional departmental pilot. It implements administrator input, automatic grouping, deterministic generation, hard validation, class/faculty/room previews and basic export. A university production roll-out additionally needs a database, authentication, timetable versions, audit logging, institutional policy configuration, bulk import and an OR-Tools CP-SAT solver. These should be delivered in phases without weakening the validator.
