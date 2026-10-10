
import json
import uuid
from pathlib import Path
from datetime import datetime


DATA_FILE = Path(__file__).parent / "study_plans.json"
LEGACY_FILE = Path(__file__).parent / "study_state.json"


def make_plan_id():
    """Create a unique ID for each study plan."""
    return uuid.uuid4().hex[:10]


def load_plans():
    """Load saved plans and migrate the previous single-plan file."""
    if DATA_FILE.exists():
        try:
            with DATA_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)

            if isinstance(data, dict) and isinstance(data.get("plans"), list):
                return data["plans"]

            if isinstance(data, list):
                return data
        except (json.JSONDecodeError, OSError):
            pass

    # Migrate the previous version's saved plan, if one exists.
    if LEGACY_FILE.exists():
        try:
            with LEGACY_FILE.open("r", encoding="utf-8") as file:
                old_data = json.load(file)

            if isinstance(old_data, dict) and old_data:
                state = old_data.get("state", old_data)

                if isinstance(state, dict) and state.get("tasks"):
                    plan = {
                        "id": make_plan_id(),
                        "name": state.get("goal", "My previous study plan"),
                        "created_at": datetime.now().isoformat(timespec="seconds"),
                        "state": state,
                    }
                    save_plans([plan])
                    return [plan]
        except (json.JSONDecodeError, OSError):
            pass

    return []


def save_plans(plans):
    """Save every plan to the local JSON data file."""
    payload = {"plans": plans}

    temporary_file = DATA_FILE.with_suffix(".tmp")

    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)

    temporary_file.replace(DATA_FILE)


def create_saved_plan(state, name=None):
    """Wrap a study plan with metadata for the plan library."""
    return {
        "id": make_plan_id(),
        "name": name or state.get("goal", "Untitled study plan"),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "state": state,
    }


def update_saved_plan(plans, plan_id, state, name=None):
    """Update one plan without changing the others."""
    updated = []

    for plan in plans:
        if plan.get("id") == plan_id:
            plan = {
                **plan,
                "name": name or plan.get("name", "Untitled study plan"),
                "state": state,
                "updated_at": datetime.now().isoformat(timespec="seconds"),
            }

        updated.append(plan)

    save_plans(updated)
    return updated


def delete_saved_plan(plans, plan_id):
    """Delete a single saved plan."""
    updated = [
        plan for plan in plans
        if plan.get("id") != plan_id
    ]

    save_plans(updated)
    return updated


# Backward-compatible helpers for the previous app version.
def load_state():
    plans = load_plans()

    if plans:
        return plans[0].get("state", {})

    return {}


def save_state(state):
    plans = load_plans()

    if plans:
        first_plan = plans[0]
        update_saved_plan(
            plans,
            first_plan["id"],
            state,
            first_plan.get("name"),
        )
    else:
        save_plans([create_saved_plan(state)])