
from datetime import date, timedelta


def decompose_tasks(subjects, goal):
    """Break each subject into manageable study tasks."""
    tasks = []

    for subject in subjects:
        subject = subject.strip()

        if not subject:
            continue

        topics = [
            f"{subject} - Learn core concepts",
            f"{subject} - Practise important questions",
            f"{subject} - Revise and self-test",
        ]

        for index, topic in enumerate(topics):
            tasks.append({
                "id": f"task_{len(tasks) + 1}",
                "subject": subject,
                "topic": topic,
                "goal": goal,
                "estimated_hours": [1.5, 1.0, 0.5][index],
                "priority": 3,
                "completed": False,
                "scheduled_date": None,
            })

    return tasks


def estimate_hours(tasks):
    """Calculate the estimated study workload."""
    return round(
        sum(float(task.get("estimated_hours", 0)) for task in tasks),
        2,
    )


def prioritize_tasks(tasks):
    """Assign simple, explainable priority scores."""
    high_priority_words = (
        "exam", "important", "difficult", "weak", "core concepts"
    )

    for task in tasks:
        topic = task.get("topic", "").lower()
        subject = task.get("subject", "").lower()

        score = 3

        if any(word in topic for word in high_priority_words):
            score += 1

        if any(word in subject for word in ("math", "programming", "physics")):
            score += 1

        task["priority"] = min(score, 5)

    return sorted(
        tasks,
        key=lambda task: (
            -int(task.get("priority", 1)),
            float(task.get("estimated_hours", 0)),
        ),
    )


def schedule_tasks(tasks, start_date, days, hours_per_day):
    """Schedule tasks without exceeding the daily hour limit."""
    start = date.fromisoformat(str(start_date))
    days = max(1, int(days))
    hours_per_day = max(0.5, float(hours_per_day))

    daily_load = [0.0] * days
    scheduled = []

    for task in tasks:
        task = task.copy()
        duration = max(0.5, float(task.get("estimated_hours", 0.5)))
        chosen_day = None

        for day_index in range(days):
            if daily_load[day_index] + duration <= hours_per_day + 1e-9:
                chosen_day = day_index
                break

        if chosen_day is None:
            task["scheduled_date"] = None
            task["schedule_status"] = "Unscheduled: daily capacity reached"
        else:
            task_date = start + timedelta(days=chosen_day)
            task["scheduled_date"] = task_date.isoformat()
            task["schedule_status"] = "Scheduled"
            daily_load[chosen_day] += duration

        scheduled.append(task)

    return scheduled


def evaluate_plan(tasks, days, hours_per_day):
    """Evaluate completion, workload, capacity and unscheduled tasks."""
    total = len(tasks)
    completed = sum(bool(task.get("completed", False)) for task in tasks)
    remaining = [
        task for task in tasks if not task.get("completed", False)
    ]

    total_hours = estimate_hours(tasks)
    remaining_hours = estimate_hours(remaining)
    unscheduled = [
        task for task in remaining
        if not task.get("scheduled_date")
    ]

    daily_load = {}
    for task in tasks:
        scheduled_date = task.get("scheduled_date")
        if scheduled_date and not task.get("completed", False):
            daily_load[scheduled_date] = (
                daily_load.get(scheduled_date, 0.0)
                + float(task.get("estimated_hours", 0))
            )

    overloaded_days = {
        day: round(hours, 2)
        for day, hours in daily_load.items()
        if hours > float(hours_per_day) + 1e-9
    }

    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "remaining_tasks": len(remaining),
        "completion_percent": round(
            completed / total * 100, 1
        ) if total else 0.0,
        "total_hours": total_hours,
        "remaining_hours": remaining_hours,
        "unscheduled_tasks": len(unscheduled),
        "overloaded_days": overloaded_days,
        "capacity_hours": round(
            max(1, int(days)) * max(0.5, float(hours_per_day)), 2
        ),
        "capacity_warning": total_hours > (
            max(1, int(days)) * max(0.5, float(hours_per_day))
        ),
    }