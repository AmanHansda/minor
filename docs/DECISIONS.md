# Design Decisions

## D1 Prototype solver
The submitted version uses a deterministic first-fit heuristic instead of OR-Tools CP-SAT. It is easier to explain in a final-year viva, has no package-install requirement, and is protected by the same validator that a CP-SAT version would use. `backend/app/solver/engine.py` is intentionally isolated so it can be replaced later.

## D2 Synthetic data
All demonstrator names and records are synthetic. Student identities are not stored.

## D3 Scope
The implemented showcase focuses on safe generation, validation, analytics, explanation, absence what-if, exports and a read-only timetable help chat. Login, database persistence, visual drag-and-drop, LLM/RAG and deployed notifications are planned extensions, not claims of completed functionality.

## D4 Chatbot
The chatbot is rule-based and reads only the generated timetable. It answers a defined set of timetable questions and cannot modify data, call an external service, or bypass validation.
