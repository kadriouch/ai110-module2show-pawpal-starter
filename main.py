from pawpal_system import Owner, Pet, Task, Scheduler

# --- Setup (tasks intentionally added out of priority/duration order) ---
owner = Owner(name="Alex", available_minutes=60)

dog = Pet(name="Biscuit", species="Dog")
dog.add_task(Task(name="Fetch in backyard", duration_minutes=20, priority="low",    frequency="daily"))
dog.add_task(Task(name="Morning walk",      duration_minutes=30, priority="high",   frequency="daily",  start_time="08:00"))
dog.add_task(Task(name="Flea medication",   duration_minutes=5,  priority="high",   frequency="weekly", start_time="08:20"))  # overlaps walk (08:00–08:30)

cat = Pet(name="Luna", species="Cat")
cat.add_task(Task(name="Laser toy play",    duration_minutes=10, priority="low",    frequency="as-needed"))
cat.add_task(Task(name="Grooming brush",    duration_minutes=15, priority="medium", frequency="weekly",  start_time="09:00"))
cat.add_task(Task(name="Feed wet food",     duration_minutes=5,  priority="high",   frequency="daily",   start_time="08:25"))  # overlaps walk (08:00–08:30)

owner.add_pet(dog)
owner.add_pet(cat)

# Mark one task complete so filter_by_status can show the difference
dog.get_tasks()[0].mark_complete()   # "Fetch in backyard" is done

scheduler = Scheduler(owner)

WIDTH = 52
SEP = "─" * WIDTH

def print_section(title: str, tasks: list):
    print(f"\n  {title}")
    print(f"  {'─' * (WIDTH - 2)}")
    if not tasks:
        print("    (none)")
    for t in tasks:
        status = "✅" if t.completed else "⬜"
        print(f"    {status} [{t.priority:6}] {t.name:<28} {t.duration_minutes:>3} min  ({t.frequency})")

# ── Standard priority-sorted plan ────────────────────────────────────────────
print(f"\n{'PawPal+ — Demo Output':^{WIDTH}}")
print(SEP)
print(f"  Owner: {owner.name}   Budget: {owner.available_minutes} min")
print(SEP)

plan = scheduler.generate_plan()
print_section("Scheduled (sorted by priority)", plan.scheduled_tasks)
if plan.skipped_tasks:
    print_section("Skipped (time ran out)", plan.skipped_tasks)
print(f"\n  Total: {plan.total_duration} min  |  Remaining: {owner.available_minutes - plan.total_duration} min")

# ── Sort by duration (shortest first) ────────────────────────────────────────
all_pending = scheduler.get_all_tasks()
by_duration = scheduler.sort_by_duration(all_pending)
print_section("Sorted by duration (shortest first)", by_duration)

# ── Filter: tasks for one pet ─────────────────────────────────────────────────
biscuit_tasks = scheduler.filter_by_pet("Biscuit")
print_section("Filter — Biscuit's pending tasks only", biscuit_tasks)

# ── Filter: pending vs completed ─────────────────────────────────────────────
completed  = scheduler.filter_by_status(completed=True)
pending    = scheduler.filter_by_status(completed=False)
print_section("Filter — completed tasks", completed)
print_section("Filter — pending tasks",   pending)

# ── Filter: by frequency ──────────────────────────────────────────────────────
daily_tasks = scheduler.filter_by_frequency("daily")
print_section("Filter — daily tasks", daily_tasks)

# ── Due today (exclude as-needed) ────────────────────────────────────────────
due = scheduler.get_due_tasks(include_as_needed=False)
print_section("Due today (excluding as-needed)", due)

# ── Conflict detection ────────────────────────────────────────────────────────
print(f"\n  Conflict detection")
print(f"  {'─' * (WIDTH - 2)}")
conflicts = scheduler.detect_conflicts()
if conflicts:
    for w in conflicts:
        print(f"    ⚠️  {w}")
else:
    print("    No conflicts detected.")

print(f"\n{SEP}\n")
