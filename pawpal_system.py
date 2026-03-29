from dataclasses import dataclass, field


@dataclass
class Owner:
    name: str
    available_minutes: int

    def set_available_time(self, minutes: int):
        self.available_minutes = minutes


@dataclass
class Task:
    name: str
    duration_minutes: int
    priority: str  # "high", "medium", or "low"
    completed: bool = False

    def mark_complete(self):
        self.completed = True


@dataclass
class Pet:
    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task):
        self.tasks.append(task)

    def get_tasks(self) -> list[Task]:
        return self.tasks


@dataclass
class DailyPlan:
    scheduled_tasks: list[Task]
    skipped_tasks: list[Task]
    explanation: str
    total_duration: int = field(init=False)

    def __post_init__(self):
        self.total_duration = sum(t.duration_minutes for t in self.scheduled_tasks)

    def display(self):
        print(self.get_summary())

    def get_summary(self) -> str:
        lines = [f"Daily Plan ({self.total_duration} min total)"]
        lines.append("\nScheduled:")
        for task in self.scheduled_tasks:
            lines.append(f"  [{task.priority}] {task.name} — {task.duration_minutes} min")
        if self.skipped_tasks:
            lines.append("\nSkipped:")
            for task in self.skipped_tasks:
                lines.append(f"  [{task.priority}] {task.name} — {task.duration_minutes} min")
        lines.append(f"\nReasoning: {self.explanation}")
        return "\n".join(lines)


class Scheduler:
    PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

    def __init__(self, owner: Owner, pet: Pet):
        self.owner = owner
        self.pet = pet

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        return sorted(tasks, key=lambda t: self.PRIORITY_ORDER.get(t.priority, 99))

    def filter_by_time(self, tasks: list[Task]) -> tuple[list[Task], list[Task]]:
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
        sorted_tasks = self.sort_by_priority(self.pet.get_tasks())
        scheduled, skipped = self.filter_by_time(sorted_tasks)
        explanation = (
            f"Tasks were sorted by priority (high → medium → low) and fitted into "
            f"{self.owner.available_minutes} minutes of available time. "
            f"{len(skipped)} task(s) were skipped due to time constraints."
        )
        return DailyPlan(scheduled, skipped, explanation)
