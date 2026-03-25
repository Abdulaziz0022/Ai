from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from student_success_copilot.models.student_profile import StudentProfile
from student_success_copilot.models.study_plan import WeeklyStudyPlan
from student_success_copilot.models.task import Task
from student_success_copilot.planning.search_planner import (
    compare_strategies,
    generate_weekly_plan,
)


def make_planning_profile() -> StudentProfile:
    return StudentProfile(
        name="Planner Case",
        tasks=[
            Task(title="Urgent essay", deadline="Monday", estimated_hours=2, priority=3),
            Task(title="Quiz revision", deadline="Tuesday", estimated_hours=2, priority=2),
            Task(title="Reading", deadline="Friday", estimated_hours=1, priority=1),
        ],
        availability={"Monday": 2.0, "Tuesday": 2.0, "Wednesday": 2.0},
        confidence=6,
        stress=5,
        attendance=85,
        quiz_score=72,
        time_spent=4,
    )


def test_planner_returns_weekly_study_plan() -> None:
    plan = generate_weekly_plan(make_planning_profile(), strategy="astar")

    assert isinstance(plan, WeeklyStudyPlan)


def test_planned_hours_do_not_exceed_available_hours() -> None:
    profile = make_planning_profile()
    plan = generate_weekly_plan(profile, strategy="astar")

    assert plan.total_planned_hours() <= profile.total_available_hours()


def test_urgent_high_priority_tasks_are_included_in_plan() -> None:
    plan = generate_weekly_plan(make_planning_profile(), strategy="astar")
    task_titles = {session.task_title for session in plan.sessions}

    assert "Urgent essay" in task_titles


def test_compare_strategies_returns_greedy_and_astar() -> None:
    results = compare_strategies(make_planning_profile())
    strategies = {result.strategy.lower() for result in results}

    assert "greedy" in strategies
    assert "astar" in strategies
