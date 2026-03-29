# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The three core actions a user should be able to perform in PawPal+ are:

1. **Enter owner and pet information** — The user provides their name, their pet's name and type, and how much time they have available today. This sets the context that the scheduler uses to build a realistic plan. Without knowing the owner's time budget, the app cannot decide which tasks fit in a given day.

2. **Add a care task** — The user creates tasks such as "morning walk," "medication," or "grooming," and specifies each task's estimated duration (in minutes) and priority level (high, medium, or low). This builds the pool of tasks from which the daily plan is drawn. Users can add as many tasks as their pet needs.

3. **Generate today's plan** — The user triggers the scheduler, which selects and orders tasks based on priority and available time, then displays the resulting daily schedule. The app also explains the reasoning — for example, why a high-priority medication task was placed before a low-priority enrichment activity, or why a long grooming session was deferred because time ran out.

**Building blocks (main objects):**

| Class | Attributes | Methods |
|-------|-----------|---------|
| `Owner` | `name`, `available_minutes` | `set_available_time()` |
| `Pet` | `name`, `species`, `tasks` (list) | `add_task()`, `get_tasks()` |
| `Task` | `name`, `duration_minutes`, `priority` ("high"/"medium"/"low"), `completed` | `mark_complete()` |
| `Scheduler` | `pet`, `owner` | `generate_plan()`, `sort_by_priority()`, `filter_by_time()` |
| `DailyPlan` | `scheduled_tasks` (list), `skipped_tasks` (list), `total_duration`, `explanation` | `display()`, `get_summary()` |

**Responsibilities:**
- `Owner` holds the time budget — the hard constraint the scheduler must respect.
- `Pet` groups tasks together and is the central entity the owner cares for.
- `Task` is the unit of work; priority and duration are the two values the scheduler acts on.
- `Scheduler` contains all scheduling logic — it decides what fits, what gets cut, and in what order.
- `DailyPlan` is the output object — a snapshot of the day's schedule plus a human-readable explanation of decisions made.

The initial design used five classes arranged in a clear data/logic/output separation:

- **`Owner`** and **`Pet`** are pure data holders. `Owner` carries the time budget; `Pet` owns the list of `Task` objects.
- **`Task`** is the atomic unit of work with `name`, `duration_minutes`, `priority`, and a `completed` flag.
- **`Scheduler`** is the only class with real logic. It receives an `Owner` and a `Pet`, sorts tasks by priority, and greedily fits them into available time.
- **`DailyPlan`** is the output object — it holds the final scheduled and skipped task lists plus a plain-language explanation of how decisions were made.

`Task` and `Pet` were implemented as Python dataclasses to eliminate boilerplate `__init__` code and make attributes self-documenting. `Scheduler` stayed a regular class because it holds logic, not data.

**b. Design changes**

After reviewing the skeleton, four potential issues were identified:

1. **Greedy skip bottleneck** — `filter_by_time` originally skipped a task the moment it didn't fit, even if later shorter tasks would have fit (e.g., a 60-min task with 10 min left would block a 5-min task). *Fix applied:* the filter now continues checking remaining tasks rather than stopping at the first one that doesn't fit.

2. **`completed` flag ignored by Scheduler** — `Task.mark_complete()` existed but the Scheduler never checked it, so already-done tasks would be re-scheduled. *Fix applied:* `filter_by_time` now skips tasks where `completed is True`.

3. **No priority validation** — `priority` is a free string. A typo like `"High"` (capital H) would silently sort to last because `PRIORITY_ORDER.get()` falls back to rank 99. *Not fixed yet — deferred to implementation phase* where a `Literal["high", "medium", "low"]` type hint or explicit validation can be added.

4. **Single-pet assumption** — `Scheduler` is initialized with exactly one `Pet`. This limits the design if a user has multiple pets. *Accepted as a known constraint* for this project scope; the architecture would need a `PetProfile` wrapper to extend.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints, applied in this order:

1. **Completion status and due date** — tasks already marked complete, or whose `next_due` date is in the future, are excluded entirely before any other logic runs. This is the highest-priority gate: there is no value in scheduling work that is already done or not yet due.

2. **Task priority** — remaining tasks are sorted high → medium → low. Within the same priority level, shorter tasks are placed first (duration as a tiebreaker) so that the owner can get more items checked off before time runs out.

3. **Available time budget** — after sorting, tasks are placed greedily into the owner's `available_minutes`. A task that doesn't fit is skipped, but the scheduler continues checking subsequent tasks in case shorter ones still fit.

Time budget was prioritised over priority ordering because scheduling a 60-minute low-priority task before a 5-minute high-priority one would be worse than the reverse — the greedy-plus-sort combination handles this naturally.

**b. Tradeoffs**

**Tradeoff: greedy scheduling (simple but not optimal)**

The `filter_by_time` method fills the schedule greedily — it walks the priority-sorted task list from top to bottom and includes each task if it fits in the remaining time. It does not search for the combination of tasks that best fills the available minutes.

*Example:* with 35 minutes available and three tasks — Task A (high, 30 min), Task B (medium, 20 min), Task C (medium, 20 min) — the greedy approach schedules A (30 min, 5 min left) and skips both B and C. The optimal solution would schedule B + C (40 min total — still over budget) or just B or C (20 min each). In this case greedy uses 30 min and optimal uses 20 min; neither is clearly "better," but greedy does guarantee that the highest-priority task always gets scheduled first.

*Why this tradeoff is reasonable:* pet care has a natural priority ordering — medication and feeding genuinely cannot wait the way enrichment or grooming can. Greedy scheduling with a priority sort respects this real-world constraint. A true optimal packing algorithm (knapsack) would be harder to understand, harder to explain to the user, and would occasionally deprioritise urgent tasks to squeeze in more total minutes. The greedy approach is also O(n log n) — fast enough for any realistic number of pet tasks.

**Evaluated AI suggestion (not accepted):** An AI review suggested replacing the O(n²) pair-loop in `detect_conflicts` with a sort-then-scan O(n log n) approach using `itertools.combinations` and a sorted event list. The performance improvement is real but irrelevant at this scale (5–20 tasks). The pair-loop is easier to read and debug, and the intent of each comparison is explicit. The more complex version was rejected in favour of readability.

---

## 3. AI Collaboration

**a. How you used AI**

AI tools were used throughout every phase, but in different roles depending on the task:

- **Design brainstorming (Phase 1)** — used to generate the initial Mermaid.js UML diagram from a plain-language description of the five classes. The prompt "create a class diagram for a pet care app with Owner, Pet, Task, Scheduler, and DailyPlan" gave a useful starting point, though several relationships (like the one-to-many Owner → Pet link) had to be corrected manually.

- **Code generation (Phase 2)** — used to convert UML sketches into Python class stubs and to suggest the switch to `@dataclass`. The dataclass suggestion was accepted immediately because it removed boilerplate without changing any logic.

- **Algorithmic review (Phase 4)** — used to audit `pawpal_system.py` and identify potential logic gaps. The prompt "review this scheduler for missing relationships or logic bottlenecks using #file:pawpal_system.py" returned four actionable issues, two of which were fixed immediately.

- **Test generation (Phase 5)** — used to draft edge-case tests from a test plan. The prompt "what are the most important edge cases to test for a pet scheduler with sorting and recurring tasks?" produced a useful structured list. The generated tests were reviewed and several were rewritten to test actual implementation behaviour rather than assumed behaviour.

The most effective prompts were **specific and file-anchored** (using `#file:` references) rather than general. Vague prompts like "improve my code" returned unhelpful suggestions; targeted ones like "how should `filter_by_time` handle a task that doesn't fit without blocking later tasks?" returned directly usable logic.

**b. Judgment and verification**

The clearest moment of rejection was the AI's suggestion to replace the O(n²) pair-loop in `detect_conflicts` with a sort-then-scan approach using `itertools.combinations`. The suggestion was technically correct and slightly more efficient, but the improvement was irrelevant at a scale of 5–20 pet tasks, and the proposed code was harder to read — the intent of each comparison was buried inside iterator unpacking. The original explicit loop was kept because clarity matters more than micro-optimisation here, and a future maintainer (or grader) should be able to understand the conflict logic without decoding combinatorics.

Verification approach: the rejected suggestion was benchmarked mentally ("does this ever run on more than 50 tasks?"), then the existing code was tested with the same edge cases (`same_start_time`, `overlapping_windows`, `adjacent_no_conflict`) to confirm it already handled them correctly. The tests passing was the final confirmation that the simpler version was sufficient.

**c. Copilot feature effectiveness**

- **Inline Chat on specific methods** — most effective for focused questions like "why would this sort behave differently for equal-priority tasks?" Kept the context narrow and the answers precise.
- **Agent Mode for larger refactors** — effective for the dataclass conversion and for wiring the full Streamlit UI. Useful when the task spanned multiple methods at once.
- **Separate chat sessions per phase** — critical for keeping context clean. The algorithmic planning session (Phase 4) didn't have the UI wiring conversation in its context, which meant suggestions stayed relevant to scheduling logic rather than drifting toward Streamlit API questions. Context pollution is a real problem in long AI sessions — starting fresh for each phase prevented it.

**d. Leading as the architect**

The most important lesson about collaborating with AI on a design task is that **AI is an excellent implementer but a poor architect**. Given a clear spec, it will produce correct and even elegant code. But left to its own scope decisions, it will over-engineer (suggesting a full knapsack solver when greedy works fine) or under-specify (generating tests that pass vacuously without testing real behaviour). The human role is to define what "correct" means, to draw the boundary between what's in scope and what isn't, and to verify that generated code actually solves the problem it was asked to solve — not just a problem that looks similar.

---

## 3e. Prompt Comparison: Multi-Model Analysis

**Task given to both models:** "Write a Python method for a `Task` dataclass that, when called after completion, automatically reschedules the task based on its frequency: daily tasks reappear tomorrow, weekly tasks reappear in 7 days, and as-needed tasks do not auto-reschedule."

---

**Model A — GPT-4o (OpenAI via ChatGPT)**

```python
def reschedule(self):
    from datetime import date, timedelta
    if self.frequency == "daily":
        self.next_due = date.today() + timedelta(days=1)
        self.completed = False
    elif self.frequency == "weekly":
        self.next_due = date.today() + timedelta(weeks=1)
        self.completed = False
    # as-needed: no change
```

*Characteristics:*
- Imports `date` and `timedelta` inside the method body (deferred import)
- Calls `date.today()` directly — no parameter for the reference date
- Resets `completed = False` after setting `next_due`, which is logically inconsistent: a completed task that has been rescheduled should remain `completed = True` until the next due date arrives
- No docstring
- Flat `if/elif` — readable but no guard clause

---

**Model B — Claude (this project's assistant)**

```python
def schedule_next(self, from_date: date | None = None) -> None:
    """
    Mark complete and set next_due using timedelta based on frequency.
    - daily   → next_due = from_date + 1 day
    - weekly  → next_due = from_date + 7 days
    - as-needed → stays completed with no next_due (owner decides when next)
    """
    base = from_date if from_date is not None else date.today()
    self.completed = True
    if self.frequency == "daily":
        self.next_due = base + timedelta(days=1)
    elif self.frequency == "weekly":
        self.next_due = base + timedelta(weeks=1)
    # as-needed: no automatic recurrence
```

*Characteristics:*
- `from_date` parameter — caller can pass a specific date, making the method deterministic and testable (no hidden `date.today()` call in tests)
- `self.completed = True` is set before scheduling, not toggled off — the task is done; `is_due()` checks `next_due` on subsequent calls
- Docstring with inline explanation per frequency case
- `base` variable makes the intent of the default clear without an `if/else` inline
- `-> None` return type annotation

---

**Comparison summary**

| Dimension | GPT-4o | Claude |
|-----------|--------|--------|
| Testability | Low — hardcoded `date.today()` | High — injectable `from_date` parameter |
| Logical correctness | Flawed — resets `completed = False` prematurely | Correct — `completed` stays `True`, `is_due()` uses `next_due` |
| Pythonic style | Basic — import inside method, no annotation | Clean — module-level import, type hint, docstring |
| Modularity | Standalone, not integrated with `is_due()` | Designed to work with `is_due()` as the single gatekeeper |

**Verdict:** The Claude version is more Pythonic and more modular. The key difference is not style — it is the design decision to keep `completed = True` after rescheduling, and to let `is_due()` be the single gate that determines whether a task appears in the pending list. The GPT-4o version toggled `completed` back to `False`, which would have caused already-completed tasks to re-appear in the schedule on the same day they were finished. This is a correctness issue, not just a style preference, and it stems from not thinking through how the method interacts with the rest of the system.

**What this illustrates:** Both models can write working Python. The difference emerges when the method must fit into an existing system with specific invariants (`is_due()` as gatekeeper, `completed` as a permanent flag within a day). A model that has context about the full system design will produce more modular output than one generating a method in isolation.

---

## 4. Testing and Verification

**a. What you tested**

The 35-test suite covered four categories of behaviour:

1. **Core task operations** — `mark_complete`, `reset`, validation on construction. These were important because `Task` is the atomic unit the entire system depends on. If `mark_complete` didn't set the flag, the scheduler would re-schedule completed tasks; if validation was absent, bad priority strings would silently corrupt sort order.

2. **Scheduling correctness** — priority sort, duration tiebreaker, time budget, multi-pet aggregation. These verified the scheduler's core contract: high-priority tasks come first, nothing scheduled exceeds available time, and tasks from all pets are considered equally.

3. **Recurrence logic** — `daily` → tomorrow, `weekly` → +7 days, `as-needed` → no recurrence, future `next_due` excluded. These were critical because recurrence is the feature most likely to have subtle off-by-one bugs. Pinning the expected date with `timedelta` made the tests precise rather than relative.

4. **Conflict detection** — same start time, overlapping windows, adjacent (no false positive), budget overflow. The no-false-positive test for adjacent tasks was the most important: a detector that flags too many conflicts would be worse than useless, as owners would ignore it.

**b. Confidence**

**★★★★☆ (4/5).** The scheduler works correctly for all tested scenarios including boundary conditions. The missing star reflects three categories of untested risk:

- Tasks whose `start_time` + `duration_minutes` wraps past midnight (e.g. a 23:50 task lasting 20 minutes)
- Concurrent Streamlit interactions where two browser tabs modify the same session state object
- Owners with a very large number of pets or tasks, where the O(n²) conflict detector's performance could become noticeable

None of these affect correctness for the intended use case, but they would be the first tests to add if this were going to production.

---

## 5. Reflection

**a. What went well**

The data/logic/output separation — `Owner`/`Pet`/`Task` as pure data, `Scheduler` as pure logic, `DailyPlan` as pure output — held up through every phase without needing to be restructured. Adding features like recurrence and conflict detection never required touching the core scheduling algorithm; they plugged in as new methods on `Scheduler` or new attributes on `Task`. That's the sign of a design with the right boundaries.

The test suite was also a genuine confidence builder. Writing the edge case tests (zero budget, exact-fit budget, future `next_due` excluded) forced a precise reading of the code and caught one implicit assumption: that `get_pending_tasks()` was filtering by `is_due()` rather than just `not completed`. Without that test, it would have been easy to miss the distinction.

**b. What you would improve**

The `start_time` field on `Task` is optional and disconnected from the scheduler — it's only used by `detect_conflicts`, not by `generate_plan`. A better design would let the scheduler assign start times automatically based on task order and a configurable day-start time (e.g. 08:00), so that the generated plan shows a real timetable rather than just a ranked list. That would also make the overlap detection genuinely useful at plan-generation time rather than only as a pre-flight check.

**c. Key takeaway**

The most important thing learned was that **designing a system means deciding what it will not do**. Every time AI suggested an enhancement — a knapsack optimiser, a full recurring-task calendar, a per-pet time budget — the right response was to ask "does this solve the actual problem a pet owner has?" Most of the time the answer was no: the problem is remembering to give medication and schedule walks, not optimising 90 minutes to the second. Keeping that constraint visible prevented scope creep and kept the codebase readable. AI tools are very good at suggesting features; the architect's job is knowing which ones to say no to.
