from dataclasses import dataclass, field
from typing import Literal

VALID_PRIORITIES = ("high", "medium", "low")
VALID_FREQUENCIES = ("daily", "weekly", "as-needed")


@dataclass
class Task:
    """A single pet care activity."""
    name: str
    duration_minutes: int
    priority: Literal["high", "medium", "low"]
    frequency: Literal["daily", "weekly", "as-needed"] = "daily"
    completed: bool = False

    def __post_init__(self):
        """Validate priority, frequency, and duration on construction."""
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(f"priority must be one of {VALID_PRIORITIES}, got '{self.priority}'")
        if self.frequency not in VALID_FREQUENCIES:
            raise ValueError(f"frequency must be one of {VALID_FREQUENCIES}, got '{self.frequency}'")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be a positive integer")

    def mark_complete(self):
        """Mark this task as done for the current day."""
        self.completed = True

    def reset(self):
        """Clear completion status (e.g. at the start of a new day)."""
        self.completed = False


@dataclass
class Pet:
    """A pet with its own list of care tasks."""
    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task):
        """Append a Task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task_name: str) -> bool:
        """Remove a task by name. Returns True if found and removed."""
        for i, task in enumerate(self.tasks):
            if task.name == task_name:
                self.tasks.pop(i)
                return True
        return False

    def get_tasks(self) -> list[Task]:
        """Return all tasks for this pet, including completed ones."""
        return self.tasks

    def get_pending_tasks(self) -> list[Task]:
        """Return only tasks not yet completed."""
        return [t for t in self.tasks if not t.completed]

    def reset_daily_tasks(self):
        """Reset completion status for all daily tasks."""
        for task in self.tasks:
            if task.frequency == "daily":
                task.reset()


@dataclass
class Owner:
    """A pet owner who may have multiple pets."""
    name: str
    available_minutes: int
    pets: list[Pet] = field(default_factory=list)

    def set_available_time(self, minutes: int):
        """Update how many minutes the owner has available today."""
        if minutes < 0:
            raise ValueError("available_minutes cannot be negative")
        self.available_minutes = minutes

    def add_pet(self, pet: Pet):
        """Register a new pet under this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> bool:
        """Remove a pet by name. Returns True if found and removed."""
        for i, pet in enumerate(self.pets):
            if pet.name == pet_name:
                self.pets.pop(i)
                return True
        return False

    def get_all_tasks(self) -> list[Task]:
        """Collect all pending tasks across every pet."""
        tasks = []
        for pet in self.pets:
            tasks.extend(pet.get_pending_tasks())
        return tasks


@dataclass
class DailyPlan:
    """The output of a scheduling run — what fits, what was skipped, and why."""
    scheduled_tasks: list[Task]
    skipped_tasks: list[Task]
    explanation: str
    total_duration: int = field(init=False)

    def __post_init__(self):
        """Compute total scheduled duration after dataclass init."""
        self.total_duration = sum(t.duration_minutes for t in self.scheduled_tasks)

    def display(self):
        """Print the plan summary to stdout."""
        print(self.get_summary())

    def get_summary(self) -> str:
        """Return a formatted multi-line string of the scheduled and skipped tasks."""
        lines = [f"Daily Plan ({self.total_duration} min total)"]
        if self.scheduled_tasks:
            lines.append("\nScheduled:")
            for task in self.scheduled_tasks:
                lines.append(f"  [{task.priority}] {task.name} — {task.duration_minutes} min ({task.frequency})")
        else:
            lines.append("\n  No tasks scheduled.")
        if self.skipped_tasks:
            lines.append("\nSkipped (insufficient time):")
            for task in self.skipped_tasks:
                lines.append(f"  [{task.priority}] {task.name} — {task.duration_minutes} min")
        lines.append(f"\nReasoning: {self.explanation}")
        return "\n".join(lines)


class Scheduler:
    """
    The scheduling brain. Retrieves all pending tasks from the owner's pets,
    sorts them by priority, and fits as many as possible into available time.
    """
    PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

    def __init__(self, owner: Owner):
        self.owner = owner

    def get_all_tasks(self) -> list[Task]:
        """Pull all pending tasks from every pet the owner has."""
        return self.owner.get_all_tasks()

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks high → medium → low, then by duration (shorter first) as a tiebreaker."""
        return sorted(
            tasks,
            key=lambda t: (self.PRIORITY_ORDER.get(t.priority, 99), t.duration_minutes),
        )

    def filter_by_time(self, tasks: list[Task]) -> tuple[list[Task], list[Task]]:
        """
        Greedily schedule tasks within available time.
        A task that doesn't fit is skipped, but shorter later tasks may still fit.
        """
        scheduled = []
        skipped = []
        time_remaining = self.owner.available_minutes
        for task in tasks:
            if task.duration_minutes <= time_remaining:
                scheduled.append(task)
                time_remaining -= task.duration_minutes
            else:
                skipped.append(task)
        return scheduled, skipped

    def generate_plan(self) -> DailyPlan:
        """Sort and fit all pending tasks; return a DailyPlan with reasoning."""
        all_tasks = self.get_all_tasks()
        sorted_tasks = self.sort_by_priority(all_tasks)
        scheduled, skipped = self.filter_by_time(sorted_tasks)

        pet_count = len(self.owner.pets)
        explanation = (
            f"Retrieved {len(all_tasks)} pending task(s) across {pet_count} pet(s). "
            f"Tasks were sorted by priority (high → medium → low), then by duration "
            f"(shorter tasks first within the same priority). "
            f"{len(scheduled)} task(s) fit within {self.owner.available_minutes} available minutes; "
            f"{len(skipped)} task(s) were skipped due to time constraints."
        )
        return DailyPlan(scheduled, skipped, explanation)

    def mark_task_complete(self, task_name: str) -> bool:
        """Find a task by name across all pets and mark it complete."""
        for pet in self.owner.pets:
            for task in pet.get_tasks():
                if task.name == task_name:
                    task.mark_complete()
                    return True
        return False
