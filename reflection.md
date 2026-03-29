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

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
