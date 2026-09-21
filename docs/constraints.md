# Implemented Constraints

| Code | Rule | Implementation |
|---|---|---|
| H1 | Required hours and lab block length | Validator totals each requirement and checks entry length. |
| H2 | Cohort does not overlap | Occupied periods are indexed by cohort. |
| H3 | Instructor does not overlap | Occupied periods are indexed by instructor. |
| H4 | Room does not overlap | Occupied periods are indexed by room. |
| H5 | Correct room type and accessibility | Room is checked against requirement. |
| H6 | Enough room capacity | Required student count is checked. |
| H7 | Labs do not cross lunch | Break period is blocked. |
| H8 | Valid periods and faculty availability | Time-grid and unavailable slots are checked. |
| H9 | Maximum weekly teaching load | Instructor total is checked. |
