"""State objects for the search-based study planner.

The planner treats weekly study scheduling as a simple search problem. Each
state keeps track of:

- how many hours are still needed for each task
- how many study hours remain on each day
- which study blocks have already been scheduled
- the path cost used by A*
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PlannedBlock:
    """A single study block placed into the partial schedule."""

    day_index: int
    task_index: int
    hours: float


@dataclass(frozen=True)
class PlanningAction:
    """An action that assigns a study block to one day and one task."""

    day_index: int
    task_index: int
    hours: float


@dataclass(frozen=True)
class PlanningState:
    """A hashable search state for weekly study planning."""

    remaining_task_hours: tuple[float, ...]
    available_day_hours: tuple[float, ...]
    scheduled_blocks: tuple[PlannedBlock, ...] = field(default_factory=tuple)
    path_cost: float = 0.0

    def total_remaining_hours(self) -> float:
        """Return the total number of task hours still unscheduled."""
        return sum(self.remaining_task_hours)

    def total_available_hours(self) -> float:
        """Return the total free study time left in the week."""
        return sum(self.available_day_hours)

    def is_goal(self) -> bool:
        """Return True when all task hours have been scheduled."""
        return all(hours <= 1e-9 for hours in self.remaining_task_hours)

    def can_expand(self) -> bool:
        """Return True when more actions are still possible."""
        return self.total_remaining_hours() > 1e-9 and self.total_available_hours() > 1e-9

    def unscheduled_hours(self) -> float:
        """Return the hours that remain unscheduled in this state."""
        return max(0.0, self.total_remaining_hours())

    def apply(self, action: PlanningAction, step_cost: float) -> "PlanningState":
        """Return the next state produced by applying one planning action."""
        next_task_hours = list(self.remaining_task_hours)
        next_day_hours = list(self.available_day_hours)

        next_task_hours[action.task_index] = max(
            0.0,
            next_task_hours[action.task_index] - action.hours,
        )
        next_day_hours[action.day_index] = max(
            0.0,
            next_day_hours[action.day_index] - action.hours,
        )

        next_block = PlannedBlock(
            day_index=action.day_index,
            task_index=action.task_index,
            hours=action.hours,
        )

        return PlanningState(
            remaining_task_hours=tuple(round(value, 4) for value in next_task_hours),
            available_day_hours=tuple(round(value, 4) for value in next_day_hours),
            scheduled_blocks=self.scheduled_blocks + (next_block,),
            path_cost=self.path_cost + step_cost,
        )
