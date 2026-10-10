# Smart Study Planner Agent

A beginner-friendly Agentic AI demonstration built with Python and Streamlit.

## What it does
- Accepts a goal, subjects, topics, available days, and hours per day.
- Decomposes topics into tasks.
- Calls priority-scoring and scheduling tools.
- Evaluates whether the plan fits the available time.
- Allows task completion tracking and replanning.
- Saves the plan locally in `study_state.json`.

## Agent workflow
**Goal → Plan → Tool calls → Evaluate → Adapt → Updated plan**

This version uses transparent local logic and does not require a paid API or claim to use an external large language model.

## Architecture
```text
User Goal
   |
Agent Controller
   |-- Task Decomposition Tool
   |-- Priority Scoring Tool
   |-- Scheduling Tool
   |-- Evaluation Tool
   |
Feasibility Check --> Accept / Adapt
   |
Saved Study Plan and Progress Tracker
```

## Run locally
1. Install Python 3.10 or later.
2. Open a terminal in this folder.
3. Create a virtual environment (optional but recommended):
   - Windows: `py -m venv .venv`
   - Windows: `.venv\\Scripts\\activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Start the app: `streamlit run app.py`

## Suggested test cases
1. One subject with two topics and three available hours.
2. Several subjects whose tasks exceed available time; check evaluation output.
3. Mark a task complete and use **Replan remaining tasks**.
4. Refresh the app and verify the saved plan remains available.

## Academic note
This is a lightweight tool-using agent prototype with explicit planning, action, evaluation, and replanning. Priority scoring is heuristic-based, not a trained model. Describe it accurately in your submission.
