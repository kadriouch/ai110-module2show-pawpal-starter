import pytest
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
