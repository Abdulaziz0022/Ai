"""Heuristic helpers for the search-based study planner."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Sequence

from student_success_copilot.models.task import Task
from student_success_copilot.planning.state import PlanningState


def build_planning_dates(
    day_names: Sequence[str],
    reference_date: date | None = None,
) -> list[date]:
    """Build concrete planning dates starting from today."""
    today = reference_date or date.today()
    return [today + timedelta(days=index) for index, _ in enumerate(day_names)]


def parse_deadline_date(
    deadline: str,
    day_names: Sequence[str],
    planning_dates: Sequence[date],
) -> date | None:
    """Parse a deadline string as either a weekday name or an ISO date."""
    explicit_date = parse_explicit_deadline_date(deadline)
    if explicit_date is not None:
        return explicit_date

    cleaned_deadline = deadline.strip()
    for day_name, planning_date in zip(day_names, planning_dates):
        if cleaned_deadline.lower() == day_name.lower():
            return planning_date

    return None


def parse_explicit_deadline_date(deadline: str) -> date | None:
    """Parse only an explicit ISO deadline date like ``2026-03-27``."""
    try:
        return datetime.strptime(deadline.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def resolve_days_left(
    task: Task,
    day_names: Sequence[str],
    planning_dates: Sequence[date],
) -> int | None:
    """Return the non-inclusive day difference until the deadline.

    If a real deadline date is present, it always wins over a typed ``days_left``
    value so scheduling stays calendar-consistent.
    """
    explicit_date = parse_explicit_deadline_date(task.deadline)
    if explicit_date is not None:
        planning_start = planning_dates[0] if planning_dates else date.today()
        return max(0, (explicit_date - planning_start).days)

    if task.days_left is not None:
        return max(0, int(task.days_left))

    deadline_date = parse_deadline_date(task.deadline, day_names, planning_dates)
    if deadline_date is None:
        return None

    planning_start = planning_dates[0] if planning_dates else date.today()
    return max(0, (deadline_date - planning_start).days)


def deadline_slot_count(
    task: Task,
    day_names: Sequence[str],
    planning_dates: Sequence[date],
) -> int | None:
    """Return how many upcoming slots count as on-time study slots.

    The logic is inclusive:
    - if ``days_left = 1``, allowed slots are today and tomorrow, so slot count is 2
    - if ``days_left = 3``, allowed slots are today plus the next 3 days, so slot count is 4

    If a real deadline date is present, the date-based result is always used.
    """
    explicit_date = parse_explicit_deadline_date(task.deadline)
    if explicit_date is not None:
        planning_start = planning_dates[0] if planning_dates else date.today()
        inclusive_days = (explicit_date - planning_start).days + 1
        return max(0, min(len(planning_dates), inclusive_days))

    if task.days_left is not None:
        inclusive_slots = int(task.days_left) + 1
        return max(0, min(len(planning_dates), inclusive_slots))

    deadline_date = parse_deadline_date(task.deadline, day_names, planning_dates)
    if deadline_date is None:
        return None

    planning_start = planning_dates[0] if planning_dates else date.today()
    inclusive_days = (deadline_date - planning_start).days + 1
    return max(0, min(len(planning_dates), inclusive_days))


def is_after_deadline_slot(
    task: Task,
    day_index: int,
    day_names: Sequence[str],
    planning_dates: Sequence[date],
) -> bool:
    """Return True when a study block falls outside the allowed deadline window."""
    slot_count = deadline_slot_count(task, day_names, planning_dates)
    if slot_count is None:
        return False
    return day_index >= slot_count


def deadline_rank(
    task: Task,
    day_names: Sequence[str],
    planning_dates: Sequence[date],
) -> int:
    """Convert a task deadline into an urgency rank where lower is more urgent."""
    slot_count = deadline_slot_count(task, day_names, planning_dates)
    if slot_count is None:
        return len(planning_dates) // 2 if planning_dates else 3
    return max(0, slot_count - 1)


def urgency_weight(
    task: Task,
    day_names: Sequence[str],
    planning_dates: Sequence[date],
) -> float:
    """Return a weight that favors earlier deadlines and higher priority."""
    rank = deadline_rank(task, day_names, planning_dates)

    if rank <= 0:
        deadline_score = 20.0
    elif rank == 1:
        deadline_score = 16.0
    elif rank == 2:
        deadline_score = 12.0
    elif rank == 3:
        deadline_score = 8.0
    else:
        deadline_score = max(2.0, 8.0 - (rank - 3))

    priority_score = 2.5 * float(task.priority)
    return deadline_score + priority_score


def remaining_work_heuristic(
    state: PlanningState,
    tasks: Sequence[Task],
    day_names: Sequence[str],
    planning_dates: Sequence[date],
) -> float:
    """Estimate how much important work remains to be scheduled."""
    score = 0.0

    for index, remaining_hours in enumerate(state.remaining_task_hours):
        if remaining_hours <= 1e-9:
            continue
        score += remaining_hours * urgency_weight(tasks[index], day_names, planning_dates)

    return score


def overdue_remaining_penalty(
    state: PlanningState,
    tasks: Sequence[Task],
    day_names: Sequence[str],
    planning_dates: Sequence[date],
) -> float:
    """Penalize states where remaining work no longer fits before deadlines."""
    penalty = 0.0

    for index, remaining_hours in enumerate(state.remaining_task_hours):
        if remaining_hours <= 1e-9:
            continue

        task = tasks[index]
        slot_count = deadline_slot_count(task, day_names, planning_dates)
        if slot_count is None:
            continue

        available_before_deadline = sum(state.available_day_hours[:slot_count])
        late_hours = max(0.0, remaining_hours - available_before_deadline)
        if late_hours > 1e-9:
            penalty += late_hours * 50.0

    return penalty


def scheduled_after_deadline_penalty(
    state: PlanningState,
    tasks: Sequence[Task],
    day_names: Sequence[str],
    planning_dates: Sequence[date],
) -> float:
    """Penalize states that already placed blocks after the deadline window."""
    penalty = 0.0

    for block in state.scheduled_blocks:
        task = tasks[block.task_index]
        if not is_after_deadline_slot(task, block.day_index, day_names, planning_dates):
            continue

        slot_count = deadline_slot_count(task, day_names, planning_dates) or 0
        slots_late = (block.day_index - slot_count) + 1
        penalty += block.hours * 90.0 * max(1, slots_late)

    return penalty


def overload_penalty(state: PlanningState) -> float:
    """Penalize states where more work remains than available time."""
    extra_hours = max(0.0, state.total_remaining_hours() - state.total_available_hours())
    return extra_hours * 14.0


def fragmentation_penalty(state: PlanningState) -> float:
    """Slightly penalize schedules with many tiny blocks."""
    return max(0, len(state.scheduled_blocks) - 4) * 0.5


def planning_heuristic(
    state: PlanningState,
    tasks: Sequence[Task],
    day_names: Sequence[str],
    planning_dates: Sequence[date],
) -> float:
    """Combined heuristic used by both Greedy search and A*."""
    return (
        remaining_work_heuristic(state, tasks, day_names, planning_dates)
        + overdue_remaining_penalty(state, tasks, day_names, planning_dates)
        + scheduled_after_deadline_penalty(state, tasks, day_names, planning_dates)
        + overload_penalty(state)
        + fragmentation_penalty(state)
    )


def action_cost(
    task: Task,
    day_index: int,
    hours: float,
    day_names: Sequence[str],
    planning_dates: Sequence[date],
) -> float:
    """Return the path-cost contribution of scheduling one study block."""
    urgency = urgency_weight(task, day_names, planning_dates)
    base_cost = ((day_index + 1) * hours) / max(urgency, 1.0)

    if is_after_deadline_slot(task, day_index, day_names, planning_dates):
        slot_count = deadline_slot_count(task, day_names, planning_dates) or 0
        slots_late = (day_index - slot_count) + 1
        return base_cost + (hours * 120.0 * max(1, slots_late))

    return base_cost + (day_index * 0.1 * hours)
