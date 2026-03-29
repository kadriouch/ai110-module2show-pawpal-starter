## PawPal+ — Final UML Class Diagram

> Paste the Mermaid code block below into https://mermaid.live to export as PNG.

```mermaid
classDiagram
    class Task {
        +String name
        +int duration_minutes
        +String priority
        +String frequency
        +bool completed
        +date next_due
        +String start_time
        +is_due(on_date) bool
        +schedule_next(from_date)
        +mark_complete()
        +reset()
    }

    class Pet {
        +String name
        +String species
        +List~Task~ tasks
        +add_task(task)
        +remove_task(task_name) bool
        +get_tasks() List~Task~
        +get_pending_tasks(on_date) List~Task~
        +reset_daily_tasks()
    }

    class Owner {
        +String name
        +int available_minutes
        +List~Pet~ pets
        +set_available_time(minutes)
        +add_pet(pet)
        +remove_pet(pet_name) bool
        +get_all_tasks() List~Task~
    }

    class DailyPlan {
        +List~Task~ scheduled_tasks
        +List~Task~ skipped_tasks
        +String explanation
        +int total_duration
        +display()
        +get_summary() String
    }

    class Scheduler {
        +Owner owner
        +PRIORITY_ORDER Dict
        +get_all_tasks() List~Task~
        +sort_by_priority(tasks) List~Task~
        +sort_by_duration(tasks) List~Task~
        +filter_by_pet(pet_name) List~Task~
        +filter_by_status(completed) List~Task~
        +filter_by_frequency(frequency) List~Task~
        +get_due_tasks(include_as_needed) List~Task~
        +filter_by_time(tasks) Tuple
        +detect_conflicts() List~String~
        +generate_plan() DailyPlan
        +mark_task_complete(task_name, on_date) bool
    }

    Owner "1" *-- "0..*" Pet : owns
    Pet "1" *-- "0..*" Task : has
    Scheduler --> Owner : reads from
    Scheduler ..> DailyPlan : produces
    DailyPlan o-- Task : references
```

## What changed from the initial design (Phase 1)

| Area | Initial design | Final design |
|------|---------------|--------------|
| `Owner` → `Pet` | One-to-one | One-to-many (`Owner` holds `List[Pet]`) |
| `Scheduler` input | `Owner` + single `Pet` | `Owner` only — aggregates all pets internally |
| `Task` attributes | `name`, `duration`, `priority`, `completed` | + `frequency`, `next_due` (date), `start_time` (HH:MM) |
| `Task` methods | `mark_complete()` | + `is_due()`, `schedule_next()`, `reset()` |
| `Pet` methods | `add_task()`, `get_tasks()` | + `remove_task()`, `get_pending_tasks(on_date)`, `reset_daily_tasks()` |
| `Owner` methods | `set_available_time()` | + `add_pet()`, `remove_pet()`, `get_all_tasks()` |
| `Scheduler` methods | `sort_by_priority()`, `filter_by_time()`, `generate_plan()` | + `sort_by_duration()`, `filter_by_pet()`, `filter_by_status()`, `filter_by_frequency()`, `get_due_tasks()`, `detect_conflicts()`, `mark_task_complete()` |
| `DailyPlan` | Output object only | Unchanged — composition arrow added to show it *references* Tasks rather than owning them |
```
