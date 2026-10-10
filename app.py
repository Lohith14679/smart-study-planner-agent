
import csv
import io
from datetime import date, datetime

import streamlit as st

from agent import StudyPlannerAgent
from storage import (
    load_plans,
    save_plans,
    create_saved_plan,
    update_saved_plan,
    delete_saved_plan,
)

st.set_page_config(
    page_title="Smart Study Planner Agent",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2.5rem;
        max-width: 1250px;
    }
    .hero {
        padding: 1.6rem;
        border-radius: 18px;
        border: 1px solid rgba(128,128,128,0.25);
        margin-bottom: 1.3rem;
    }
    .hero h1 { margin-bottom: 0.3rem; }
    .muted { opacity: 0.75; }
    </style>
    """,
    unsafe_allow_html=True,
)

if "plans" not in st.session_state:
    st.session_state.plans = load_plans()

if "active_plan_id" not in st.session_state:
    st.session_state.active_plan_id = (
        st.session_state.plans[0]["id"]
        if st.session_state.plans else None
    )

if "agent_log" not in st.session_state:
    st.session_state.agent_log = []


def persist_plans():
    save_plans(st.session_state.plans)


def get_active_plan():
    for plan in st.session_state.plans:
        if plan.get("id") == st.session_state.active_plan_id:
            return plan
    return None


def get_evaluation(state):
    tasks = state.get("tasks", [])
    total = len(tasks)
    completed = sum(bool(task.get("completed")) for task in tasks)
    remaining = [task for task in tasks if not task.get("completed")]

    total_hours = sum(
        float(task.get("estimated_hours", 0)) for task in tasks
    )
    remaining_hours = sum(
        float(task.get("estimated_hours", 0)) for task in remaining
    )

    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "remaining_tasks": len(remaining),
        "completion_percent": round(completed / total * 100, 1) if total else 0,
        "total_hours": round(total_hours, 2),
        "remaining_hours": round(remaining_hours, 2),
        "unscheduled_tasks": sum(
            not task.get("scheduled_date") for task in remaining
        ),
    }


def csv_report(state):
    output = io.StringIO()
    fields = [
        "subject",
        "topic",
        "priority",
        "estimated_hours",
        "scheduled_date",
        "completed",
        "schedule_status",
    ]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()

    for task in state.get("tasks", []):
        writer.writerow({
            key: task.get(key, "")
            for key in fields
        })

    return output.getvalue()


def text_report(plan):
    state = plan["state"]
    evaluation = get_evaluation(state)

    lines = [
        "SMART STUDY PLANNER AGENT",
        "=" * 32,
        f"Plan: {plan.get('name', 'Study plan')}",
        f"Goal: {state.get('goal', '')}",
        f"Subjects: {', '.join(state.get('subjects', []))}",
        f"Created: {plan.get('created_at', '')}",
        "",
        "PROGRESS SUMMARY",
        "-" * 32,
        f"Tasks: {evaluation['total_tasks']}",
        f"Completed: {evaluation['completed_tasks']}",
        f"Remaining: {evaluation['remaining_tasks']}",
        f"Completion: {evaluation['completion_percent']}%",
        f"Total estimated hours: {evaluation['total_hours']}",
        f"Remaining estimated hours: {evaluation['remaining_hours']}",
        f"Unscheduled tasks: {evaluation['unscheduled_tasks']}",
        "",
        "TASK SCHEDULE",
        "-" * 32,
    ]

    for task in state.get("tasks", []):
        status = "Completed" if task.get("completed") else "Pending"
        lines.append(
            f"[{status}] {task.get('topic', '')} | "
            f"Date: {task.get('scheduled_date') or 'Unscheduled'} | "
            f"Hours: {task.get('estimated_hours', 0)} | "
            f"Priority: {task.get('priority', 0)}"
        )

    lines.extend([
        "",
        "NOTE",
        "This is a rule-based planning tool. Estimates are suggestions; "
        "review the schedule and adjust it to your actual needs.",
    ])

    return "\n".join(lines)


# Sidebar: plan library
with st.sidebar:
    st.markdown("## 📚 Plan Library")
    st.caption("Your plans are stored locally on this computer.")

    if st.session_state.plans:
        plan_labels = {
            plan["id"]: plan.get("name", "Untitled plan")
            for plan in st.session_state.plans
        }

        ids = list(plan_labels.keys())
        current_id = (
            st.session_state.active_plan_id
            if st.session_state.active_plan_id in ids
            else ids[0]
        )

        selected_id = st.selectbox(
            "Open a saved plan",
            options=ids,
            index=ids.index(current_id),
            format_func=lambda item: plan_labels[item],
            key="plan_selector",
        )
        st.session_state.active_plan_id = selected_id

        if st.button("🗑️ Delete selected plan", use_container_width=True):
            st.session_state.plans = delete_saved_plan(
                st.session_state.plans, selected_id
            )
            st.session_state.active_plan_id = (
                st.session_state.plans[0]["id"]
                if st.session_state.plans else None
            )
            st.session_state.agent_log = []
            st.rerun()
    else:
        st.info("No saved plans yet. Create your first plan below.")

    st.divider()
    st.caption("Agent pipeline")
    st.markdown(
        "1. Analyse goal\n\n"
        "2. Decompose tasks\n\n"
        "3. Prioritise\n\n"
        "4. Schedule\n\n"
        "5. Evaluate and replan"
    )


st.markdown(
    """
    <div class="hero">
        <h1>📚 Smart Study Planner Agent</h1>
        <p>Plan smarter, track your progress, and reorganise unfinished work.</p>
        <span class="muted">An explainable, rule-based AI-agent demonstration</span>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_create, tab_dashboard, tab_schedule, tab_reports, tab_architecture = st.tabs([
    "✨ Create Plan",
    "📊 Dashboard",
    "🗓️ Schedule",
    "📥 Reports",
    "🧠 Agent Design",
])


# Create plan
with tab_create:
    st.subheader("Create a study plan")
    st.write("Describe your goal and the subjects you want to study.")

    with st.form("create_plan_form", clear_on_submit=False):
        goal = st.text_input(
            "Study goal",
            placeholder="Example: Prepare for my semester examinations",
        )
        subjects_text = st.text_area(
            "Subjects (one per line)",
            placeholder="Mathematics\nProgramming\nPhysics",
            height=120,
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            days = st.number_input(
                "Planning period (days)", min_value=1, max_value=180, value=7
            )
        with col2:
            hours_per_day = st.number_input(
                "Available hours per day",
                min_value=0.5,
                max_value=16.0,
                value=3.0,
                step=0.5,
            )
        with col3:
            start_date = st.date_input("Start date", value=date.today())

        plan_name = st.text_input(
            "Plan name",
            placeholder="Example: November Semester Exams",
        )

        submitted = st.form_submit_button(
            "🤖 Generate Study Plan",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        subjects = [
            line.strip()
            for line in subjects_text.splitlines()
            if line.strip()
        ]

        if not goal.strip():
            st.error("Please enter a study goal.")
        elif not subjects:
            st.error("Please enter at least one subject.")
        else:
            agent = StudyPlannerAgent()
            result = agent.run(
                goal=goal.strip(),
                subjects=subjects,
                days=int(days),
                hours_per_day=float(hours_per_day),
                start_date=start_date.isoformat(),
            )

            state = result["state"]
            name = plan_name.strip() or goal.strip()

            new_plan = create_saved_plan(state, name)
            st.session_state.plans.append(new_plan)
            st.session_state.active_plan_id = new_plan["id"]
            st.session_state.agent_log = result["log"]
            persist_plans()

            st.success("Study plan created and saved!")
            st.rerun()


# Resolve active plan after possible changes in the sidebar
active_plan = get_active_plan()

with tab_dashboard:
    st.subheader("Progress dashboard")

    if not active_plan:
        st.info("Create a plan first to see your dashboard.")
    else:
        state = active_plan["state"]
        evaluation = get_evaluation(state)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total tasks", evaluation["total_tasks"])
        m2.metric("Completed", evaluation["completed_tasks"])
        m3.metric("Remaining", evaluation["remaining_tasks"])
        m4.metric("Hours remaining", evaluation["remaining_hours"])

        st.progress(
            min(1.0, evaluation["completion_percent"] / 100),
            text=f"{evaluation['completion_percent']}% complete",
        )

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Workload")
            st.write(f"Total estimated workload: **{evaluation['total_hours']} hours**")
            st.write(f"Remaining workload: **{evaluation['remaining_hours']} hours**")
            st.write(f"Planning capacity: **{state.get('days', 0) * state.get('hours_per_day', 0)} hours**")

        with col2:
            st.markdown("#### Plan health")
            if evaluation["unscheduled_tasks"]:
                st.warning(
                    f"{evaluation['unscheduled_tasks']} unfinished task(s) "
                    "need a date. Consider replanning or increasing your study time."
                )
            elif evaluation["remaining_tasks"] == 0:
                st.success("All tasks are complete. Excellent work!")
            else:
                st.success("All unfinished tasks currently have scheduled dates.")

        subject_progress = {}
        for task in state.get("tasks", []):
            subject = task.get("subject", "Other")
            stats = subject_progress.setdefault(subject, [0, 0])
            stats[1] += 1
            stats[0] += int(bool(task.get("completed")))

        st.markdown("#### Progress by subject")
        for subject, (done, total) in subject_progress.items():
            st.write(f"**{subject}** — {done}/{total} tasks")
            st.progress(done / total if total else 0)

        if st.button("💾 Refresh saved plan statistics"):
            persist_plans()
            st.success("Saved.")


# Schedule and completion tracking
with tab_schedule:
    st.subheader("Task schedule")

    if not active_plan:
        st.info("Create or open a saved plan first.")
    else:
        state = active_plan["state"]
        tasks = state.get("tasks", [])

        filter_choice = st.radio(
            "Show tasks",
            ["All", "Pending", "Completed", "Unscheduled"],
            horizontal=True,
        )

        visible_tasks = []
        for index, task in enumerate(tasks):
            completed = bool(task.get("completed"))
            if filter_choice == "Pending" and completed:
                continue
            if filter_choice == "Completed" and not completed:
                continue
            if filter_choice == "Unscheduled" and (
                task.get("scheduled_date") or completed
            ):
                continue
            visible_tasks.append((index, task))

        if not visible_tasks:
            st.info("No tasks match this filter.")
        else:
            for index, task in visible_tasks:
                task_id = task.get("id", str(index))
                label = (
                    f"{task.get('topic', 'Study task')} · "
                    f"{task.get('estimated_hours', 0)} h · "
                    f"{task.get('scheduled_date') or 'Unscheduled'}"
                )
                new_completed = st.checkbox(
                    label,
                    value=bool(task.get("completed", False)),
                    key=f"complete_{active_plan['id']}_{task_id}",
                )

                if new_completed != bool(task.get("completed", False)):
                    task["completed"] = new_completed
                    task["completed_at"] = (
                        datetime.now().isoformat(timespec="seconds")
                        if new_completed else None
                    )
                    persist_plans()
                    st.rerun()

                st.caption(
                    f"Subject: {task.get('subject', 'N/A')} · "
                    f"Priority: {task.get('priority', 0)}/5 · "
                    f"Status: {task.get('schedule_status', 'Scheduled')}"
                )

        st.divider()

        if st.button("🔄 Automatically Replan Remaining Tasks", type="primary"):
            result = StudyPlannerAgent().replan(state)
            active_plan["state"] = result["state"]
            active_plan["updated_at"] = datetime.now().isoformat(timespec="seconds")
            st.session_state.agent_log = result["log"]
            persist_plans()
            st.success("Unfinished tasks have been rescheduled.")
            st.rerun()


# Downloadable reports
with tab_reports:
    st.subheader("Download reports")

    if not active_plan:
        st.info("Create or open a saved plan first.")
    else:
        state = active_plan["state"]
        safe_name = "".join(
            character if character.isalnum() else "_"
            for character in active_plan.get("name", "study_plan")
        ).strip("_") or "study_plan"

        st.write("Export your schedule for reviewing, printing, or submitting.")

        st.download_button(
            "⬇️ Download task schedule (CSV)",
            data=csv_report(state),
            file_name=f"{safe_name}_tasks.csv",
            mime="text/csv",
            use_container_width=True,
        )

        st.download_button(
            "⬇️ Download readable study report (TXT)",
            data=text_report(active_plan),
            file_name=f"{safe_name}_report.txt",
            mime="text/plain",
            use_container_width=True,
        )

        st.markdown("#### Report preview")
        st.text(text_report(active_plan))


# Architecture and explainability
with tab_architecture:
    st.subheader("Agent architecture")
    st.write(
        "The agent uses transparent rules rather than an external generative "
        "AI service. It makes decisions through a repeatable pipeline."
    )

    st.code(
        """
        User goal and subjects
                 |
                 v
           Task Decomposition
                 |
                 v
           Priority Assignment
                 |
                 v
            Task Scheduler
                 |
                 v
          Plan Evaluation
                 |
          +------+------+
          |             |
          v             v
      Fits capacity   Over capacity
          |             |
          v             v
       Save Plan    Adjust Estimates
          |             |
          +------<------+
                 |
                 v
        Dashboard / Reports
                 |
                 v
        User marks progress
                 |
                 v
        Replan unfinished tasks
        """,
        language="text",
    )

    st.markdown("#### Agent decision log")
    if st.session_state.agent_log:
        for entry in st.session_state.agent_log:
            st.write(f"• {entry}")
    else:
        st.caption("Generate or replan a study plan to populate the activity log.")

    st.markdown("#### Current plan configuration")
    if active_plan:
        st.json({
            "goal": active_plan["state"].get("goal"),
            "subjects": active_plan["state"].get("subjects"),
            "days": active_plan["state"].get("days"),
            "hours_per_day": active_plan["state"].get("hours_per_day"),
            "saved_plan_id": active_plan["id"],
        })
    else:
        st.caption("No active plan.")