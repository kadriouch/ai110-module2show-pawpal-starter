# 🐾 PawPal+

**PawPal+** is a Streamlit app that helps a busy pet owner stay consistent with daily pet care. It generates a prioritised daily schedule across multiple pets, detects scheduling conflicts, and automatically reschedules recurring tasks.

---

## 📸 Demo

<a href="/course_images/ai110/pawpal_screenshot.png" target="_blank">
  <img src='/course_images/ai110/pawpal_screenshot.png' title='PawPal App' width='' alt='PawPal App' class='center-block' />
</a>

---

## Features

### Owner & pet management
- Register an owner with a daily time budget (in minutes)
- Add and manage multiple pets (name + species)
- Tasks are organised per pet and aggregated for scheduling

### Task management
- Create tasks with **name**, **duration**, **priority** (`high` / `medium` / `low`), and **frequency** (`daily` / `weekly` / `as-needed`)
- Optionally assign a **start time** (`HH:MM`) to enable time-overlap detection
- View all tasks per pet in a table showing status, next due date, and frequency

### Priority-based scheduling
- Tasks are sorted **high → medium → low**, with duration as a tiebreaker (shorter tasks of equal priority go first)
- Alternative **shortest-first** sort mode maximises the number of tasks completed when time is tight
- Greedy time-budget fitting: tasks that don't fit are skipped, but the scheduler continues to check shorter tasks that might still fit

### Automatic recurring tasks
- Completing a `daily` task automatically sets its next due date to **tomorrow**
- Completing a `weekly` task sets its next due date to **+7 days** via Python's `timedelta`
- `as-needed` tasks complete without auto-rescheduling — the owner decides when next

### Conflict detection
Three types of warnings (displayed before you generate the plan, never crashes the app):
1. **Budget overflow** — high-priority tasks combined exceed available time
2. **Duplicate names** — same task name used across different pets
3. **Time overlap** — two timed tasks have intersecting scheduled windows

### Explained scheduling
Every generated plan includes a plain-language **reasoning block** that explains how many tasks were retrieved, what sort order was used, how many fit, and how many were skipped.

---

## Project structure

```
pawpal_system.py   — core logic: Task, Pet, Owner, DailyPlan, Scheduler
app.py             — Streamlit UI
main.py            — CLI demo / testing ground
tests/
  test_pawpal.py   — 35 automated pytest tests
uml_final.md       — final Mermaid.js UML diagram (paste at mermaid.live for PNG)
reflection.md      — design decisions and tradeoffs
```

---

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

---

## Testing PawPal+

```bash
python -m pytest        # all 35 tests
python -m pytest -v     # verbose output
```

**What the tests cover (35 tests total):**

| Group | Count | Description |
|-------|-------|-------------|
| Task behaviour | 5 | `mark_complete`, `reset`, validation (bad priority, zero duration) |
| Pet behaviour | 5 | `add_task`, `remove_task`, pending task filtering |
| Scheduler — core | 5 | Priority ordering, time budget, skip logic, multi-pet aggregation |
| Sorting correctness | 4 | Priority sort, duration tiebreaker, `sort_by_duration`, all-same-priority case |
| Recurrence logic | 5 | Daily → tomorrow, weekly → +7 days, as-needed → no recurrence, future `next_due` excluded |
| Conflict detection | 5 | Same start time, overlapping windows, adjacent tasks (no false positive), budget overflow |
| Edge cases | 6 | Empty pet, empty owner, zero budget, exact-fit budget, all tasks completed, invalid `start_time` |

**Confidence level: ★★★★☆ (4/5)**

The scheduler handles all tested scenarios correctly, including boundary conditions (exact-fit budget, future due dates, adjacent non-overlapping tasks). One star withheld because real-world usage could surface untested combinations — tasks spanning midnight, owners with dozens of pets, or concurrent UI interactions modifying session state.

---

## Optional Extension: Data Persistence

PawPal+ automatically saves your owner, pets, and tasks to `data.json` and reloads them on the next run — no manual export needed.

### How it works

Each class exposes a `to_dict()` / `from_dict()` pair for JSON-safe serialisation. `date` objects are stored as ISO-format strings (`"2026-04-05"`) and converted back on load. No third-party libraries required.

```python
owner.save_to_json("data.json")      # writes data.json
owner = Owner.load_from_json("data.json")  # restores full state
```

`load_from_json` returns `None` (instead of raising) if the file is missing or corrupt — so a fresh run always starts cleanly.

In `app.py`, a `save()` helper is called automatically after every mutation — saving owner info, adding a pet, or adding a task — so the file is always in sync with the UI.

### How Agent Mode was used

Agent Mode was prompted with:

> *"Add save_to_json and load_from_json methods to the Owner class in #file:pawpal_system.py, then update the Streamlit state in #file:app.py to load this data on startup."*

Agent Mode suggested using `marshmallow` for schema-based serialisation. That was rejected in favour of a custom `to_dict` / `from_dict` approach: marshmallow adds a dependency and a schema layer that duplicates the dataclass field definitions. The custom approach is 30 lines, zero dependencies, and handles the only non-trivial type (`date` → ISO string) in one line per field.

The `current_pet` pointer restoration (re-linking the selected pet after a page reload) was not in the Agent Mode output and was added manually — a good example of where AI-generated code needs a human to think through the stateful edge cases.

---

## Optional Extension: Weighted Task Scoring

> *Implemented via Agent Mode — see below for how AI was used.*

A third sort mode, **Weighted score**, is available alongside Priority and Duration in the schedule generator.

### How it works

Each task receives a numeric score computed by `Scheduler.score_task()`:

```
score = priority_weight + frequency_weight + efficiency_bonus

priority_weight:  high=10, medium=5, low=2
frequency_weight: daily=4,  weekly=2, as-needed=1
efficiency_bonus: 1 / duration_minutes
```

Tasks are then sorted highest-score first by `sort_by_weight()`.

**Why this is better than binary priority for some scenarios:**

| Scenario | Priority sort | Weighted sort |
|----------|--------------|---------------|
| High-priority weekly grooming vs medium-priority daily feeding | Grooming always first | Feeding scores higher (daily urgency) |
| Two high-priority tasks, one 5 min, one 60 min | 5 min first (duration tiebreaker) | 5 min scores much higher (efficiency bonus = 0.2 vs 0.017) |
| Low-priority daily walk vs medium-priority as-needed grooming | Grooming first | Walk scores higher (daily recurrence = +4 vs +1) |

The weighted mode is most useful when an owner has a mix of frequencies and doesn't want infrequent high-priority tasks to permanently dominate daily essentials.

### How Agent Mode was used to implement this

Agent Mode was used to explore the design space before writing any code. The prompt was:

> *"Based on my scheduler in #file:pawpal_system.py, suggest a third algorithmic capability that goes beyond sorting by priority or duration. It should be explainable to a non-technical pet owner and produce a meaningfully different schedule."*

Agent Mode returned three candidates:
1. **Weighted scoring** — combine priority, frequency, and duration into a numeric rank
2. **Next available slot** — find the earliest time block a task can start given existing timed tasks
3. **Deadline-aware scheduling** — treat `next_due` as a soft deadline and boost score as the date approaches

Weighted scoring was chosen because it produces a different result to priority sort in realistic scenarios (daily medium tasks vs weekly high tasks), is explainable in plain English, and adds no new data to `Task`. The scoring formula was drafted by Agent Mode and then hand-tuned: the original suggestion used equal weights (5/5/5) which made frequency nearly irrelevant at scale — the values were adjusted to 10/4/variable to give priority the dominant role while still letting frequency and duration influence close calls.

The four new tests were also drafted with AI assistance and then reviewed to confirm they test observable behaviour rather than just the formula's arithmetic.

---

## Smarter Scheduling (algorithm reference)

**Sorting**
- `sort_by_priority()` — high → medium → low; duration tiebreaker within same priority
- `sort_by_duration()` — shortest-first; maximises task count within the time budget

**Filtering**
- `filter_by_pet(name)` — pending tasks for one pet only
- `filter_by_status(completed)` — split done vs. pending across all pets
- `filter_by_frequency(frequency)` — tasks matching `"daily"`, `"weekly"`, or `"as-needed"`
- `get_due_tasks(include_as_needed)` — only tasks due today; optionally include on-demand tasks

**Conflict detection**
- Budget overflow, duplicate names, and time-window overlap — all return warning strings, never raise

---

## UML

See [uml_final.md](uml_final.md) for the final Mermaid.js class diagram and a table of design changes from the initial sketch to the final implementation.
