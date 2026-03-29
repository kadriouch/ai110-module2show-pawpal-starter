# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Smarter Scheduling

Beyond basic priority sorting, `pawpal_system.py` includes several algorithmic enhancements in the `Scheduler` class:

**Sorting**
- `sort_by_priority()` — orders tasks high → medium → low, using duration as a tiebreaker (shorter tasks of equal priority go first to maximise throughput).
- `sort_by_duration()` — orders tasks shortest-first, useful when the goal is to complete as many tasks as possible regardless of priority.

**Filtering**
- `filter_by_pet(name)` — returns only pending tasks belonging to a specific pet.
- `filter_by_status(completed)` — separates done tasks from pending ones across all pets.
- `filter_by_frequency(frequency)` — returns tasks matching `"daily"`, `"weekly"`, or `"as-needed"`.
- `get_due_tasks(include_as_needed)` — returns only tasks that are actually due today, with an option to include on-demand tasks.

**Recurring tasks**
Each `Task` has an optional `start_time` (`"HH:MM"`) and a `next_due` date. Calling `mark_task_complete()` on the scheduler automatically sets the next occurrence using `timedelta`:
- `daily` → next due tomorrow
- `weekly` → next due in 7 days
- `as-needed` → no automatic recurrence

**Conflict detection**
`detect_conflicts()` returns human-readable warning strings (never raises) for three scenarios:
1. High-priority tasks combined exceed the owner's available time budget.
2. Duplicate task names exist across different pets.
3. Two timed tasks have overlapping scheduled windows (uses `start_time` + `duration_minutes`).
