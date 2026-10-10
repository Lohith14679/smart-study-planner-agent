
from datetime import date, timedelta

from tools import (
    decompose_tasks,
    estimate_hours,
    prioritize_tasks,
    schedule_tasks,
    evaluate_plan,
)


class StudyPlannerAgent:
    """
    A rule-based study planning agent.

    It breaks a goal into tasks, prioritizes them, schedules them,
    evaluates the result, and can replan unfinished tasks.
    """

    def run(
        self,
        goal,
        subjects,
        days,
        hours_per_day,
        previous_state=None,
        start_date=None,
    ):
        start_date = start_date or date.today().isoformat()
        days = max(1, int(days))
        hours_per_day = max(0.5, float(hours_per_day))

        log = [
            "Step 1: Analysed the study goal.",
            "Step 2: Broke subjects into study tasks.",
        ]

        tasks = decompose_tasks(subjects, goal)
        tasks = prioritize_tasks(tasks)
        log.append("Step 3: Ranked tasks using transparent priority rules.")

        # Preserve completed work if the same plan is being regenerated.
        if previous_state:
            old_tasks = {
                task.get("id"): task
                for task in previous_state.get("tasks", [])
            }

            for task in tasks:
                old_task = old_tasks.get(task.get("id"))

                if old_task and old_task.get("completed"):
                    task["completed"] = True

        tasks = schedule_tasks(
            tasks,
            start_date,
            days,
            hours_per_day,
        )
        log.append("Step 4: Scheduled tasks within daily capacity where possible.")

        evaluation = evaluate_plan(tasks, days, hours_per_day)

        # If the requested workload exceeds capacity, reduce estimated
        # durations gradually and evaluate again. This is a heuristic,
        # so the app still reports any unscheduled tasks.
        if evaluation["capacity_warning"]:
            log.append(
                "Step 5: Workload exceeds available capacity. "
                "Attempting a more compact estimate."
            )

            for task in tasks:
                task["estimated_hours"] = max(
                    0.5,
                    round(float(task["estimated_hours"]) * 0.8, 2),
                )

            tasks = schedule_tasks(
                tasks,
                start_date,
                days,
                hours_per_day,
            )
            evaluation = evaluate_plan(tasks, days, hours_per_day)

            log.append(
                "Re-estimated task durations. Review the estimates "
                "and any unscheduled tasks before relying on the plan."
            )
        else:
            log.append("Step 5: Checked the workload against available capacity.")

        state = {
            "goal": goal,
            "subjects": subjects,
            "days": days,
            "hours_per_day": hours_per_day,
            "start_date": start_date,
            "tasks": tasks,
            "evaluation": evaluation,
            "updated_at": date.today().isoformat(),
        }

        log.append(
            f"Evaluation complete: {evaluation['completed_tasks']} of "
            f"{evaluation['total_tasks']} tasks completed."
        )

        return {
            "state": state,
            "log": log,
            "summary": evaluation,
        }

    def replan(self, state):
        """Reschedule only unfinished tasks while retaining completed work."""
        tasks = state.get("tasks", [])
        remaining = [
            task.copy()
            for task in tasks
            if not task.get("completed", False)
        ]
        completed = [
            task.copy()
            for task in tasks
            if task.get("completed", False)
        ]

        days = max(1, int(state.get("days", 1)))
        hours_per_day = max(0.5, float(state.get("hours_per_day", 1)))
        new_start = date.today().isoformat()

        log = [
            f"Found {len(completed)} completed tasks.",
            f"Found {len(remaining)} unfinished tasks.",
            "Rescheduling unfinished tasks from today.",
        ]

        # Keep existing estimates and priority order.
        remaining = prioritize_tasks(remaining)
        rescheduled = schedule_tasks(
            remaining,
            new_start,
            days,
            hours_per_day,
        )

        # Completed tasks remain in the plan and keep their original dates.
        combined = completed + rescheduled
        evaluation = evaluate_plan(combined, days, hours_per_day)

        updated_state = {
            **state,
            "start_date": new_start,
            "tasks": combined,
            "evaluation": evaluation,
            "updated_at": date.today().isoformat(),
        }

        log.append(
            f"Replanning finished. {evaluation['unscheduled_tasks']} "
            "unfinished tasks could not be scheduled."
        )

        return {
            "state": updated_state,
            "log": log,
            "summary": evaluation,
        }