"""Heuristic helpers for the search-based study planner."""

from __future__ import annotations

from datetime import date, datetime
from typing import Sequence

from student_success_copilot import config
from student_success_copilot.models.task import Task
from student_success_copilot.planning.state import PlanningState


def deadline_rank(deadline: str, day_names: Sequence[str] | None = None) -> int:
    """Convert a deadline string into a simple urgency rank.

    Lower numbers mean a more urgent deadline.
    """
    study_days = list(day_names or config.DEFAULT_STUDY_DAYS)
    cleaned_deadline = deadline.strip()

    for index, day in enumerate(study_days):
        if cleaned_deadline.lower() == day.lower():
            return index

    try:
        target_date = datetime.strptime(cleaned_deadline, "%Y-%m-%d").date()
        delta_days = (target_date - date.today()).days
        return max(0, min(len(study_days) + 3, delta_days))
    except ValueError:
        return len(study_days) // 2


def urgency_weight(task: Task, day_names: Sequence[str] | None = None) -> float:
    """Return a weight that favors urgent and high-priority tasks."""
    rank = deadline_rank(task.deadline, day_names)
    deadline_score = max(1.0, 8.0 - rank)
    priority_score = 1.0 + float(task.priority)
    return deadline_score + priority_score


def remaining_work_heuristic(
    state: PlanningState,
    tasks: Sequence[Task],
    day_names: Sequence[str] | None = None,
) -> float:
    """Estimate how much important work remains to be scheduled."""
    score = 0.0

    for index, remaining_hours in enumerate(state.remaining_task_hours):
        if remaining_hours <= 1e-9:
            continue
        score += remaining_hours * urgency_weight(tasks[index], day_names)

    return score


def overload_penalty(state: PlanningState) -> float:
    """Penalize states where more work remains than available time."""
    extra_hours = max(0.0, state.total_remaining_hours() - state.total_available_hours())
    return extra_hours * 12.0


def fragmentation_penalty(state: PlanningState) -> float:
    """Slightly penalize long schedules with many tiny blocks."""
    return max(0, len(state.scheduled_blocks) - 4) * 0.5


def planning_heuristic(
    state: PlanningState,
    tasks: Sequence[Task],
    day_names: Sequence[str] | None = None,
) -> float:
    """Combined heuristic used by both Greedy search and A*."""
    return (
        remaining_work_heuristic(state, tasks, day_names)
        + overload_penalty(state)
        + fragmentation_penalty(state)
    )


def action_cost(
    task: Task,
    day_index: int,
    hours: float,
    day_names: Sequence[str] | None = None,
) -> float:
    """Return the path-cost contribution of scheduling one study block.

    Lower cost is better. Urgent or high-priority tasks scheduled earlier in the
    week get a lower cost, which helps A* prefer them.
    """
    weight = urgency_weight(task, day_names)
    return ((day_index + 1) * hours) / max(weight, 1.0)
