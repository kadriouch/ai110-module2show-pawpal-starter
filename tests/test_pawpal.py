import pytest
from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler


# --- Fixtures ---

@pytest.fixture
def sample_task():
    return Task(name="Morning walk", duration_minutes=30, priority="high")

@pytest.fixture
def sample_pet():
    return Pet(name="Biscuit", species="Dog")

@pytest.fixture
def owner_with_pets():
    owner = Owner(name="Alex", available_minutes=60)
    dog = Pet(name="Biscuit", species="Dog")
    dog.add_task(Task(name="Walk",       duration_minutes=30, priority="high"))
    dog.add_task(Task(name="Medication", duration_minutes=5,  priority="high"))
    dog.add_task(Task(name="Play fetch", duration_minutes=20, priority="low"))
    owner.add_pet(dog)
    return owner


# --- Task tests ---

def test_mark_complete_changes_status(sample_task):
    assert sample_task.completed is False
    sample_task.mark_complete()
    assert sample_task.completed is True

def test_mark_complete_is_idempotent(sample_task):
    sample_task.mark_complete()
    sample_task.mark_complete()
    assert sample_task.completed is True

def test_task_reset_clears_completion(sample_task):
    sample_task.mark_complete()
    sample_task.reset()
    assert sample_task.completed is False

def test_task_invalid_priority_raises():
    with pytest.raises(ValueError):
        Task(name="Bad task", duration_minutes=10, priority="urgent")

def test_task_zero_duration_raises():
    with pytest.raises(ValueError):
        Task(name="Bad task", duration_minutes=0, priority="high")


# --- Pet tests ---

def test_add_task_increases_count(sample_pet, sample_task):
    assert len(sample_pet.get_tasks()) == 0
    sample_pet.add_task(sample_task)
    assert len(sample_pet.get_tasks()) == 1

def test_add_multiple_tasks(sample_pet):
    sample_pet.add_task(Task(name="Walk",  duration_minutes=30, priority="high"))
    sample_pet.add_task(Task(name="Feed",  duration_minutes=5,  priority="high"))
    sample_pet.add_task(Task(name="Brush", duration_minutes=15, priority="medium"))
    assert len(sample_pet.get_tasks()) == 3

def test_remove_task_decreases_count(sample_pet, sample_task):
    sample_pet.add_task(sample_task)
    removed = sample_pet.remove_task("Morning walk")
    assert removed is True
    assert len(sample_pet.get_tasks()) == 0

def test_remove_nonexistent_task_returns_false(sample_pet):
    assert sample_pet.remove_task("Ghost task") is False

def test_get_pending_tasks_excludes_completed(sample_pet):
    t1 = Task(name="Walk", duration_minutes=30, priority="high")
    t2 = Task(name="Feed", duration_minutes=5,  priority="high")
    t1.mark_complete()
    sample_pet.add_task(t1)
    sample_pet.add_task(t2)
    assert len(sample_pet.get_pending_tasks()) == 1


# --- Scheduler tests ---

def test_scheduler_schedules_high_priority_first(owner_with_pets):
    scheduler = Scheduler(owner_with_pets)
    plan = scheduler.generate_plan()
    priorities = [t.priority for t in plan.scheduled_tasks]
    high_indices = [i for i, p in enumerate(priorities) if p == "high"]
    low_indices  = [i for i, p in enumerate(priorities) if p == "low"]
    assert max(high_indices) < min(low_indices)

def test_scheduler_respects_time_budget():
    owner = Owner(name="Alex", available_minutes=10)
    pet = Pet(name="Biscuit", species="Dog")
    pet.add_task(Task(name="Long walk", duration_minutes=60, priority="high"))
    pet.add_task(Task(name="Feed",      duration_minutes=5,  priority="high"))
    owner.add_pet(pet)
    plan = Scheduler(owner).generate_plan()
    assert plan.total_duration <= owner.available_minutes

def test_scheduler_skips_when_over_budget():
    owner = Owner(name="Alex", available_minutes=10)
    pet = Pet(name="Biscuit", species="Dog")
    pet.add_task(Task(name="Long walk", duration_minutes=60, priority="high"))
    owner.add_pet(pet)
    plan = Scheduler(owner).generate_plan()
    assert len(plan.skipped_tasks) == 1
    assert plan.scheduled_tasks == []

def test_scheduler_excludes_completed_tasks(owner_with_pets):
    scheduler = Scheduler(owner_with_pets)
    scheduler.mark_task_complete("Walk")
    plan = scheduler.generate_plan()
    scheduled_names = [t.name for t in plan.scheduled_tasks]
    assert "Walk" not in scheduled_names

def test_scheduler_aggregates_tasks_across_pets():
    owner = Owner(name="Alex", available_minutes=120)
    dog = Pet(name="Biscuit", species="Dog")
    dog.add_task(Task(name="Walk", duration_minutes=30, priority="high"))
    cat = Pet(name="Luna", species="Cat")
    cat.add_task(Task(name="Feed", duration_minutes=5, priority="high"))
    owner.add_pet(dog)
    owner.add_pet(cat)
    plan = Scheduler(owner).generate_plan()
    scheduled_names = [t.name for t in plan.scheduled_tasks]
    assert "Walk" in scheduled_names
    assert "Feed" in scheduled_names


# ── Sorting correctness ───────────────────────────────────────────────────────

def test_sort_by_priority_order():
    """High tasks appear before medium, medium before low."""
    owner = Owner(name="Alex", available_minutes=120)
    pet = Pet(name="Biscuit", species="Dog")
    pet.add_task(Task(name="Play",  duration_minutes=10, priority="low"))
    pet.add_task(Task(name="Brush", duration_minutes=15, priority="medium"))
    pet.add_task(Task(name="Meds",  duration_minutes=5,  priority="high"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    sorted_tasks = scheduler.sort_by_priority(pet.get_pending_tasks())
    priorities = [t.priority for t in sorted_tasks]
    assert priorities == ["high", "medium", "low"]

def test_sort_by_priority_duration_tiebreaker():
    """Within the same priority, shorter tasks come first."""
    owner = Owner(name="Alex", available_minutes=120)
    pet = Pet(name="Biscuit", species="Dog")
    pet.add_task(Task(name="Long walk", duration_minutes=30, priority="high"))
    pet.add_task(Task(name="Meds",      duration_minutes=5,  priority="high"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    sorted_tasks = scheduler.sort_by_priority(pet.get_pending_tasks())
    assert sorted_tasks[0].name == "Meds"
    assert sorted_tasks[1].name == "Long walk"

def test_sort_by_duration_shortest_first():
    """sort_by_duration returns tasks ordered shortest to longest."""
    owner = Owner(name="Alex", available_minutes=120)
    pet = Pet(name="Biscuit", species="Dog")
    pet.add_task(Task(name="Walk",  duration_minutes=30, priority="high"))
    pet.add_task(Task(name="Meds",  duration_minutes=5,  priority="high"))
    pet.add_task(Task(name="Brush", duration_minutes=15, priority="medium"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    sorted_tasks = scheduler.sort_by_duration(pet.get_pending_tasks())
    durations = [t.duration_minutes for t in sorted_tasks]
    assert durations == sorted(durations)

def test_all_same_priority_sorted_by_duration():
    """When all priorities are equal, the shortest task is scheduled first."""
    owner = Owner(name="Alex", available_minutes=120)
    pet = Pet(name="Biscuit", species="Dog")
    pet.add_task(Task(name="C", duration_minutes=20, priority="medium"))
    pet.add_task(Task(name="A", duration_minutes=5,  priority="medium"))
    pet.add_task(Task(name="B", duration_minutes=10, priority="medium"))
    owner.add_pet(pet)
    plan = Scheduler(owner).generate_plan()
    names = [t.name for t in plan.scheduled_tasks]
    assert names == ["A", "B", "C"]


# ── Recurrence logic ──────────────────────────────────────────────────────────

def test_daily_task_next_due_is_tomorrow():
    """Completing a daily task sets next_due to today + 1 day."""
    today = date.today()
    owner = Owner(name="Alex", available_minutes=60)
    pet = Pet(name="Biscuit", species="Dog")
    task = Task(name="Walk", duration_minutes=30, priority="high", frequency="daily")
    pet.add_task(task)
    owner.add_pet(pet)
    Scheduler(owner).mark_task_complete("Walk", on_date=today)
    assert task.next_due == today + timedelta(days=1)
    assert task.completed is True

def test_weekly_task_next_due_is_next_week():
    """Completing a weekly task sets next_due to today + 7 days."""
    today = date.today()
    owner = Owner(name="Alex", available_minutes=60)
    pet = Pet(name="Biscuit", species="Dog")
    task = Task(name="Grooming", duration_minutes=20, priority="medium", frequency="weekly")
    pet.add_task(task)
    owner.add_pet(pet)
    Scheduler(owner).mark_task_complete("Grooming", on_date=today)
    assert task.next_due == today + timedelta(weeks=1)

def test_as_needed_task_no_auto_recurrence():
    """Completing an as-needed task does not set a next_due date."""
    today = date.today()
    owner = Owner(name="Alex", available_minutes=60)
    pet = Pet(name="Biscuit", species="Dog")
    task = Task(name="Bath", duration_minutes=30, priority="low", frequency="as-needed")
    pet.add_task(task)
    owner.add_pet(pet)
    Scheduler(owner).mark_task_complete("Bath", on_date=today)
    assert task.next_due is None
    assert task.completed is True

def test_future_next_due_excluded_from_pending():
    """A task with next_due in the future is not returned as pending."""
    tomorrow = date.today() + timedelta(days=1)
    task = Task(name="Walk", duration_minutes=30, priority="high",
                frequency="daily", next_due=tomorrow)
    pet = Pet(name="Biscuit", species="Dog")
    pet.add_task(task)
    assert task not in pet.get_pending_tasks()

def test_completed_daily_task_absent_from_next_plan():
    """After marking a daily task complete, it does not appear in the next generate_plan()."""
    today = date.today()
    owner = Owner(name="Alex", available_minutes=60)
    pet = Pet(name="Biscuit", species="Dog")
    pet.add_task(Task(name="Walk", duration_minutes=30, priority="high", frequency="daily"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    scheduler.mark_task_complete("Walk", on_date=today)
    plan = scheduler.generate_plan()
    assert all(t.name != "Walk" for t in plan.scheduled_tasks)


# ── Conflict detection ────────────────────────────────────────────────────────

def test_conflict_same_start_time():
    """Two tasks at identical start times are flagged as overlapping."""
    owner = Owner(name="Alex", available_minutes=120)
    pet = Pet(name="Biscuit", species="Dog")
    pet.add_task(Task(name="Walk", duration_minutes=30, priority="high",   start_time="08:00"))
    pet.add_task(Task(name="Meds", duration_minutes=5,  priority="high",   start_time="08:00"))
    owner.add_pet(pet)
    conflicts = Scheduler(owner).detect_conflicts()
    assert any("Walk" in w and "Meds" in w for w in conflicts)

def test_conflict_overlapping_windows():
    """A task starting inside another task's window is flagged."""
    owner = Owner(name="Alex", available_minutes=120)
    pet = Pet(name="Biscuit", species="Dog")
    pet.add_task(Task(name="Walk", duration_minutes=30, priority="high", start_time="08:00"))
    pet.add_task(Task(name="Feed", duration_minutes=5,  priority="high", start_time="08:20"))
    owner.add_pet(pet)
    conflicts = Scheduler(owner).detect_conflicts()
    assert any("Walk" in w and "Feed" in w for w in conflicts)

def test_no_conflict_adjacent_tasks():
    """Tasks that touch but do not overlap are not flagged."""
    owner = Owner(name="Alex", available_minutes=120)
    pet = Pet(name="Biscuit", species="Dog")
    pet.add_task(Task(name="Walk", duration_minutes=30, priority="high", start_time="08:00"))
    pet.add_task(Task(name="Feed", duration_minutes=5,  priority="high", start_time="08:30"))
    owner.add_pet(pet)
    conflicts = Scheduler(owner).detect_conflicts()
    overlap_warnings = [w for w in conflicts if "Time conflict" in w]
    assert overlap_warnings == []

def test_conflict_high_priority_exceeds_budget():
    """detect_conflicts warns when high-priority tasks alone exceed available time."""
    owner = Owner(name="Alex", available_minutes=10)
    pet = Pet(name="Biscuit", species="Dog")
    pet.add_task(Task(name="Walk", duration_minutes=30, priority="high"))
    pet.add_task(Task(name="Meds", duration_minutes=20, priority="high"))
    owner.add_pet(pet)
    conflicts = Scheduler(owner).detect_conflicts()
    assert any("High-priority" in w for w in conflicts)

def test_no_conflict_tasks_without_start_time():
    """Tasks without start_time never trigger a time-overlap warning."""
    owner = Owner(name="Alex", available_minutes=120)
    pet = Pet(name="Biscuit", species="Dog")
    pet.add_task(Task(name="Walk", duration_minutes=30, priority="high"))
    pet.add_task(Task(name="Meds", duration_minutes=5,  priority="high"))
    owner.add_pet(pet)
    conflicts = Scheduler(owner).detect_conflicts()
    overlap_warnings = [w for w in conflicts if "Time conflict" in w]
    assert overlap_warnings == []


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_pet_with_no_tasks():
    """A pet with no tasks returns an empty pending list without crashing."""
    pet = Pet(name="Ghost", species="Cat")
    assert pet.get_pending_tasks() == []

def test_owner_with_no_pets():
    """An owner with no pets produces an empty plan without crashing."""
    owner = Owner(name="Alex", available_minutes=60)
    plan = Scheduler(owner).generate_plan()
    assert plan.scheduled_tasks == []
    assert plan.skipped_tasks == []
    assert plan.total_duration == 0

def test_zero_available_minutes():
    """With zero time available, every task is skipped."""
    owner = Owner(name="Alex", available_minutes=0)
    pet = Pet(name="Biscuit", species="Dog")
    pet.add_task(Task(name="Walk", duration_minutes=30, priority="high"))
    owner.add_pet(pet)
    plan = Scheduler(owner).generate_plan()
    assert plan.scheduled_tasks == []
    assert len(plan.skipped_tasks) == 1
    assert plan.total_duration == 0

def test_task_exactly_fills_budget():
    """A task whose duration equals available_minutes is scheduled, not skipped."""
    owner = Owner(name="Alex", available_minutes=30)
    pet = Pet(name="Biscuit", species="Dog")
    pet.add_task(Task(name="Walk", duration_minutes=30, priority="high"))
    owner.add_pet(pet)
    plan = Scheduler(owner).generate_plan()
    assert len(plan.scheduled_tasks) == 1
    assert plan.total_duration == 30

def test_all_tasks_already_completed():
    """When all tasks are done, generate_plan returns an empty schedule."""
    owner = Owner(name="Alex", available_minutes=60)
    pet = Pet(name="Biscuit", species="Dog")
    task = Task(name="Walk", duration_minutes=30, priority="high")
    task.mark_complete()
    pet.add_task(task)
    owner.add_pet(pet)
    plan = Scheduler(owner).generate_plan()
    assert plan.scheduled_tasks == []

def test_invalid_start_time_raises():
    """A malformed start_time string raises ValueError on Task construction."""
    with pytest.raises(ValueError):
        Task(name="Walk", duration_minutes=30, priority="high", start_time="8:00am")


# ── Weighted scoring ──────────────────────────────────────────────────────────

def test_score_task_high_daily_scores_above_low_asneeded():
    """A high-priority daily task should score higher than a low-priority as-needed task."""
    owner = Owner(name="Alex", available_minutes=120)
    scheduler = Scheduler(owner)
    urgent = Task(name="Meds",  duration_minutes=5,  priority="high",   frequency="daily")
    casual = Task(name="Brush", duration_minutes=15, priority="low",    frequency="as-needed")
    assert scheduler.score_task(urgent) > scheduler.score_task(casual)

def test_score_task_efficiency_bonus_favours_shorter():
    """Two tasks with identical priority and frequency: shorter one scores higher."""
    owner = Owner(name="Alex", available_minutes=120)
    scheduler = Scheduler(owner)
    short = Task(name="Quick feed", duration_minutes=5,  priority="medium", frequency="daily")
    long  = Task(name="Long walk",  duration_minutes=60, priority="medium", frequency="daily")
    assert scheduler.score_task(short) > scheduler.score_task(long)

def test_sort_by_weight_orders_highest_score_first():
    """sort_by_weight returns tasks highest-score first."""
    owner = Owner(name="Alex", available_minutes=120)
    pet = Pet(name="Biscuit", species="Dog")
    pet.add_task(Task(name="Play",      duration_minutes=20, priority="low",    frequency="as-needed"))
    pet.add_task(Task(name="Meds",      duration_minutes=5,  priority="high",   frequency="daily"))
    pet.add_task(Task(name="Grooming",  duration_minutes=15, priority="medium", frequency="weekly"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    ranked = scheduler.sort_by_weight(pet.get_pending_tasks())
    scores = [scheduler.score_task(t) for t in ranked]
    assert scores == sorted(scores, reverse=True)

def test_sort_by_weight_daily_medium_beats_weekly_medium():
    """A medium daily task scores higher than a medium weekly task (frequency matters)."""
    owner = Owner(name="Alex", available_minutes=120)
    scheduler = Scheduler(owner)
    daily  = Task(name="Feed",  duration_minutes=5, priority="medium", frequency="daily")
    weekly = Task(name="Brush", duration_minutes=5, priority="medium", frequency="weekly")
    assert scheduler.score_task(daily) > scheduler.score_task(weekly)
