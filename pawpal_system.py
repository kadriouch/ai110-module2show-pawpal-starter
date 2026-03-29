from dataclasses import dataclass, field
from datetime import date, timedelta
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
    next_due: date | None = None       # None means due immediately (today)
    start_time: str | None = None      # Optional "HH:MM" — e.g. "08:00"

    def __post_init__(self):
        """Validate priority, frequency, duration, and start_time on construction."""
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(f"priority must be one of {VALID_PRIORITIES}, got '{self.priority}'")
        if self.frequency not in VALID_FREQUENCIES:
            raise ValueError(f"frequency must be one of {VALID_FREQUENCIES}, got '{self.frequency}'")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be a positive integer")
        if self.start_time is not None:
            try:
                h, m = self.start_time.split(":")
                if not (0 <= int(h) <= 23 and 0 <= int(m) <= 59):
                    raise ValueError
            except (ValueError, AttributeError):
                raise ValueError(f"start_time must be 'HH:MM', got '{self.start_time}'")

    def is_due(self, on_date: date | None = None) -> bool:
        """Return True if this task is due on the given date (defaults to today)."""
        if self.completed:
            return False
        if self.next_due is None:
            return True
        check = on_date if on_date is not None else date.today()
        return self.next_due <= check

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

    def mark_complete(self):
        """Mark this task as done for the current day."""
        self.completed = True

    def reset(self):
        """Clear completion status and next_due (e.g. at the start of a new day)."""
        self.completed = False
        self.next_due = None


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

    def get_pending_tasks(self, on_date: date | None = None) -> list[Task]:
        """Return only tasks that are due and not yet completed on the given date (defaults to today)."""
        return [t for t in self.tasks if t.is_due(on_date)]

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
        """Initialise the scheduler with an Owner whose pets and tasks it will manage."""
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

    def sort_by_duration(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks shortest-first to maximise the number of tasks that fit in the budget."""
        return sorted(tasks, key=lambda t: t.duration_minutes)

    def filter_by_pet(self, pet_name: str) -> list[Task]:
        """Return all pending tasks belonging to the named pet."""
        for pet in self.owner.pets:
            if pet.name == pet_name:
                return pet.get_pending_tasks()
        return []

    def filter_by_status(self, completed: bool) -> list[Task]:
        """Return tasks across all pets filtered by completion status."""
        return [
            task
            for pet in self.owner.pets
            for task in pet.get_tasks()
            if task.completed == completed
        ]

    def filter_by_frequency(self, frequency: str) -> list[Task]:
        """Return all pending tasks matching the given frequency ('daily', 'weekly', 'as-needed')."""
        return [
            task
            for pet in self.owner.pets
            for task in pet.get_pending_tasks()
            if task.frequency == frequency
        ]

    def get_due_tasks(self, include_as_needed: bool = False) -> list[Task]:
        """
        Return tasks that are due for scheduling today.
        Daily tasks are always included; weekly and as-needed tasks only when opted in.
        """
        due = []
        for pet in self.owner.pets:
            for task in pet.get_pending_tasks():
                if task.frequency == "daily":
                    due.append(task)
                elif task.frequency == "weekly":
                    due.append(task)
                elif task.frequency == "as-needed" and include_as_needed:
                    due.append(task)
        return due

    @staticmethod
    def _to_minutes(hhmm: str) -> int:
        """Convert 'HH:MM' string to total minutes since midnight."""
        h, m = hhmm.split(":")
        return int(h) * 60 + int(m)

    def detect_conflicts(self) -> list[str]:
        """
        Return warning strings (never raises) for three conflict types:
        1. High-priority tasks alone exceed the available time budget.
        2. Duplicate task names found across different pets.
        3. Two timed tasks overlap (their scheduled windows intersect).
        """
        warnings = []

        # Conflict 1: high-priority tasks exceed the time budget on their own
        high_priority_tasks = [
            t for pet in self.owner.pets
            for t in pet.get_pending_tasks()
            if t.priority == "high"
        ]
        high_total = sum(t.duration_minutes for t in high_priority_tasks)
        if high_total > self.owner.available_minutes:
            warnings.append(
                f"High-priority tasks total {high_total} min but only "
                f"{self.owner.available_minutes} min are available — "
                f"some high-priority tasks will be skipped."
            )

        # Conflict 2: duplicate task names across different pets
        seen: dict[str, str] = {}  # task_name → first pet name
        for pet in self.owner.pets:
            for task in pet.get_tasks():
                if task.name in seen and seen[task.name] != pet.name:
                    warnings.append(
                        f"Duplicate task name '{task.name}' found on both "
                        f"'{seen[task.name]}' and '{pet.name}'."
                    )
                else:
                    seen[task.name] = pet.name

        # Conflict 3: overlapping timed tasks
        # Collect all pending tasks that have a start_time, tagged with their pet
        timed: list[tuple[Task, str]] = []
        for pet in self.owner.pets:
            for task in pet.get_pending_tasks():
                if task.start_time is not None:
                    timed.append((task, pet.name))

        # Check every pair — two tasks overlap when one starts before the other ends
        for i in range(len(timed)):
            for j in range(i + 1, len(timed)):
                a, a_pet = timed[i]
                b, b_pet = timed[j]
                a_start = self._to_minutes(a.start_time)
                a_end   = a_start + a.duration_minutes
                b_start = self._to_minutes(b.start_time)
                b_end   = b_start + b.duration_minutes
                if a_start < b_end and b_start < a_end:
                    warnings.append(
                        f"Time conflict: '{a.name}' ({a_pet}, {a.start_time}–"
                        f"{a_end // 60:02d}:{a_end % 60:02d}) overlaps with "
                        f"'{b.name}' ({b_pet}, {b.start_time}–"
                        f"{b_end // 60:02d}:{b_end % 60:02d})."
                    )

        return warnings

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

    def mark_task_complete(self, task_name: str, on_date: date | None = None) -> bool:
        """
        Find a task by name across all pets, mark it complete, and schedule
        its next occurrence using timedelta based on its frequency.
        """
        for pet in self.owner.pets:
            for task in pet.get_tasks():
                if task.name == task_name:
                    task.schedule_next(from_date=on_date)
                    return True
        return False
