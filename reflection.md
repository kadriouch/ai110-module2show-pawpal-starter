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

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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
