# Design Decisions

## D1 Prototype solver
The submitted version uses a deterministic first-fit heuristic instead of OR-Tools CP-SAT. It is easier to explain in a final-year viva, has no package-install requirement, and is protected by the same validator that a CP-SAT version would use. `backend/app/solver/engine.py` is intentionally isolated so it can be replaced later.

## D2 Synthetic data
All demonstrator names and records are synthetic. Student identities are not stored.

## D3 Scope
The implemented showcase focuses on safe generation, validation, analytics, explanation, absence what-if, exports and a read-only timetable help chat. Login, database persistence, visual drag-and-drop, LLM/RAG and deployed notifications are planned extensions, not claims of completed functionality.

## D4 Chatbot
The chatbot is rule-based and reads only the generated timetable. It answers a defined set of timetable questions and cannot modify data, call an external service, or bypass validation.

## D5 Soft Preference and Gap Optimization in Candidate Slot Ranking
Candidate slots are ranked deterministically by scoring instructor preferences (bonus for preferred slots), cohort class adjacency (bonus for slots adjacent to existing classes on that day to eliminate idle gaps), and slight penalty for un-preferred period 1 slots. Hard constraints (H1–H9) remain strictly enforced by `validator.py`.

## D6 Anti-Slop Academic Console Art Direction
Follows `tasteskill v2` app-screen principles: flat surfaces bounded by clean 1px rules, zero blurry drop shadows, color strictly reserved for data state (forest green for Feasible, crimson for Infeasible, amber for multi-hour labs, neutral lunch break column), formal high-legibility typography for official university sheets, and full print-ready stylesheets.

## D7 Universal Weekly Grid Sheets & Per-Entity Exports
All three core scheduling perspectives (Academic Class, Faculty Member, and Classroom/Lab) are rendered as complete weekly Day × Period grids with lunch breaks and metadata. Dedicated export endpoints (`/api/export/class/<group>`, `/api/export/teacher/<id>`, `/api/export/room/<id>`) enable official distribution by the Timetable Office.
