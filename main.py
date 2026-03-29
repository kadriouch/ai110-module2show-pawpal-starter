from pawpal_system import Owner, Pet, Task, Scheduler

# --- Setup ---
owner = Owner(name="Alex", available_minutes=90)

dog = Pet(name="Biscuit", species="Dog")
dog.add_task(Task(name="Morning walk",      duration_minutes=30, priority="high",   frequency="daily"))
dog.add_task(Task(name="Flea medication",   duration_minutes=5,  priority="high",   frequency="weekly"))
dog.add_task(Task(name="Fetch in backyard", duration_minutes=20, priority="low",    frequency="daily"))

cat = Pet(name="Luna", species="Cat")
cat.add_task(Task(name="Feed wet food",     duration_minutes=5,  priority="high",   frequency="daily"))
cat.add_task(Task(name="Grooming brush",    duration_minutes=15, priority="medium", frequency="weekly"))
cat.add_task(Task(name="Laser toy play",    duration_minutes=10, priority="low",    frequency="as-needed"))

owner.add_pet(dog)
owner.add_pet(cat)

# --- Schedule ---
scheduler = Scheduler(owner)
plan = scheduler.generate_plan()

# --- Display ---
WIDTH = 52
SEP = "─" * WIDTH

print(f"\n{'PawPal+ — Today\'s Schedule':^{WIDTH}}")
print(SEP)
print(f"  Owner : {owner.name}")
print(f"  Budget: {owner.available_minutes} min available")
print(SEP)

if plan.scheduled_tasks:
    print(f"  {'TASK':<28} {'PRIORITY':<10} {'MIN':>4}")
    print(f"  {'----':<28} {'--------':<10} {'---':>4}")
    for task in plan.scheduled_tasks:
        print(f"  {task.name:<28} {task.priority:<10} {task.duration_minutes:>4}")
else:
    print("  No tasks could be scheduled.")

print(SEP)
print(f"  Total scheduled : {plan.total_duration} min")
print(f"  Time remaining  : {owner.available_minutes - plan.total_duration} min")

if plan.skipped_tasks:
    print(f"\n  Skipped ({len(plan.skipped_tasks)} task(s) — insufficient time):")
    for task in plan.skipped_tasks:
        print(f"    - {task.name} [{task.priority}] — {task.duration_minutes} min")

print(f"\n  Reasoning:\n  {plan.explanation}\n")
