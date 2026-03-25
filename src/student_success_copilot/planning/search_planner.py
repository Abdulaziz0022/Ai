"""Search-based planner for building a weekly study plan."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from heapq import heappop, heappush
from itertools import count
from typing import Sequence

from student_success_copilot import config
from student_success_copilot.models.student_profile import StudentProfile
from student_success_copilot.models.study_plan import StudySession, WeeklyStudyPlan
from student_success_copilot.models.task import Task
from student_success_copilot.planning.heuristics import (
    action_cost,
    build_planning_dates,
    deadline_rank,
    deadline_slot_count,
    is_after_deadline_slot,
    planning_heuristic,
    resolve_days_left,
)
from student_success_copilot.planning.state import PlanningAction, PlanningState


@dataclass
class PlanningResult:
    """Store a planner run so it can be inspected later."""

    strategy: str
    final_state: PlanningState
    weekly_plan: WeeklyStudyPlan
    explored_states: int
    goal_reached: bool

    @property
    def unscheduled_hours(self) -> float:
        """Return the number of task hours that could not be scheduled."""
        return self.final_state.unscheduled_hours()

    def to_summary_line(self) -> str:
        """Return a short comparison line for coursework reporting."""
        status = "complete" if self.goal_reached else "partial"
        return (
            f"{self.strategy.upper()}: {status} plan, explored "
            f"{self.explored_states} state(s), planned "
            f"{self.weekly_plan.total_planned_hours():.1f} hour(s), unscheduled "
            f"{self.unscheduled_hours:.1f} hour(s)."
        )


class SearchPlanner:
    """Plan weekly study sessions using Greedy or A* search."""

    def __init__(
        self,
        profile: StudentProfile,
        strategy: str = "astar",
        session_length: float | None = None,
        day_names: Sequence[str] | None = None,
    ) -> None:
        self.profile = profile
        self.strategy = strategy.lower()
        self.session_length = session_length or config.DEFAULT_SESSION_LENGTH_HOURS
        self.day_names = _ordered_day_names_from_today(day_names or config.DEFAULT_STUDY_DAYS)
        self.planning_dates = build_planning_dates(self.day_names, reference_date=date.today())
        self.tasks = _ordered_tasks(profile.tasks, self.day_names, self.planning_dates)
        self._state_counter = count()

    def create_initial_state(self) -> PlanningState:
        """Build the first planning state from the student profile."""
        day_hours = [float(self.profile.availability.get(day, 0.0)) for day in self.day_names]
        task_hours = [float(task.estimated_hours) for task in self.tasks]
        return PlanningState(
            remaining_task_hours=tuple(task_hours),
            available_day_hours=tuple(day_hours),
        )

    def generate_actions(self, state: PlanningState) -> list[PlanningAction]:
        """Generate all legal next actions from the current state."""
        if not state.can_expand():
            return []

        task_indices = sorted(
            (
                index
                for index, remaining in enumerate(state.remaining_task_hours)
                if remaining > 1e-9
            ),
            key=lambda index: _task_sort_key(
                self.tasks[index],
                self.day_names,
                self.planning_dates,
            ),
        )

        actions: list[PlanningAction] = []

        for task_index in task_indices:
            remaining_task_hours = state.remaining_task_hours[task_index]
            candidate_day_indices = self._ordered_day_indices_for_task(task_index, state)

            for day_index in candidate_day_indices:
                free_day_hours = state.available_day_hours[day_index]
                if free_day_hours <= 1e-9:
                    continue

                block_hours = min(
                    self.session_length,
                    remaining_task_hours,
                    free_day_hours,
                )
                if block_hours <= 1e-9:
                    continue

                actions.append(
                    PlanningAction(
                        day_index=day_index,
                        task_index=task_index,
                        hours=round(block_hours, 2),
                    )
                )

        actions.sort(
            key=lambda action: (
                _task_sort_key(
                    self.tasks[action.task_index],
                    self.day_names,
                    self.planning_dates,
                ),
                self._day_preference_key(action.task_index, action.day_index),
                -action.hours,
            )
        )
        return actions

    def is_goal_state(self, state: PlanningState) -> bool:
        """Return True when all task hours are scheduled."""
        return state.is_goal()

    def heuristic(self, state: PlanningState) -> float:
        """Return the heuristic estimate for the current state."""
        return planning_heuristic(
            state,
            self.tasks,
            self.day_names,
            self.planning_dates,
        )

    def step_cost(self, action: PlanningAction) -> float:
        """Return the path-cost added by a single action."""
        task = self.tasks[action.task_index]
        return action_cost(
            task,
            action.day_index,
            action.hours,
            self.day_names,
            self.planning_dates,
        )

    def evaluate_priority(self, state: PlanningState) -> float:
        """Return the priority value used in the search frontier."""
        if self.strategy == "greedy":
            return self.heuristic(state)
        if self.strategy == "astar":
            return state.path_cost + self.heuristic(state)
        raise ValueError("Unknown search strategy. Use 'greedy' or 'astar'.")

    def search(self, max_states: int = 4000) -> PlanningResult:
        """Run the search and return the best weekly plan found."""
        initial_state = self.create_initial_state()

        if not self.tasks:
            plan = WeeklyStudyPlan()
            plan.notes.append("No tasks were provided, so no study sessions were scheduled.")
            return PlanningResult(
                strategy=self.strategy,
                final_state=initial_state,
                weekly_plan=plan,
                explored_states=1,
                goal_reached=True,
            )

        frontier: list[tuple[float, int, PlanningState]] = []
        heappush(
            frontier,
            (self.evaluate_priority(initial_state), next(self._state_counter), initial_state),
        )

        best_costs: dict[tuple[tuple[float, ...], tuple[float, ...]], float] = {
            self._state_key(initial_state): initial_state.path_cost
        }
        explored_states = 0
        best_state = initial_state

        while frontier and explored_states < max_states:
            _, _, current_state = heappop(frontier)
            explored_states += 1

            if self._is_better_state(current_state, best_state):
                best_state = current_state

            if self.is_goal_state(current_state):
                best_state = current_state
                break

            for action in self.generate_actions(current_state):
                next_state = current_state.apply(action, self.step_cost(action))
                state_key = self._state_key(next_state)
                known_cost = best_costs.get(state_key)

                if known_cost is not None and known_cost <= next_state.path_cost:
                    continue

                best_costs[state_key] = next_state.path_cost
                priority = self.evaluate_priority(next_state)
                heappush(frontier, (priority, next(self._state_counter), next_state))

        plan = self._build_weekly_plan(best_state, explored_states)
        return PlanningResult(
            strategy=self.strategy,
            final_state=best_state,
            weekly_plan=plan,
            explored_states=explored_states,
            goal_reached=best_state.is_goal(),
        )

    def _ordered_day_indices_for_task(
        self,
        task_index: int,
        state: PlanningState,
    ) -> list[int]:
        """Return valid day indices for one task."""
        all_candidate_days = [
            index for index, hours in enumerate(state.available_day_hours) if hours > 1e-9
        ]

        on_time_days = [
            day_index
            for day_index in all_candidate_days
            if not is_after_deadline_slot(
                self.tasks[task_index],
                day_index,
                self.day_names,
                self.planning_dates,
            )
        ]

        if on_time_days:
            return sorted(on_time_days)

        late_days = [
            day_index
            for day_index in all_candidate_days
            if is_after_deadline_slot(
                self.tasks[task_index],
                day_index,
                self.day_names,
                self.planning_dates,
            )
        ]
        return sorted(
            late_days,
            key=lambda day_index: self._day_preference_key(task_index, day_index),
        )

    def _day_preference_key(self, task_index: int, day_index: int) -> tuple[int, int]:
        """Prefer earlier on-time slots and heavily separate late slots."""
        task = self.tasks[task_index]
        slot_count = deadline_slot_count(task, self.day_names, self.planning_dates)

        if slot_count is None:
            return (0, day_index)

        if day_index < slot_count:
            return (0, day_index)

        slots_late = (day_index - slot_count) + 1
        return (100 + slots_late, day_index)

    def _build_weekly_plan(
        self,
        final_state: PlanningState,
        explored_states: int,
    ) -> WeeklyStudyPlan:
        """Convert the final search state into the shared WeeklyStudyPlan model."""
        plan = WeeklyStudyPlan()
        merged_blocks: dict[tuple[int, int], float] = {}

        for block in final_state.scheduled_blocks:
            merged_blocks[(block.day_index, block.task_index)] = (
                merged_blocks.get((block.day_index, block.task_index), 0.0) + block.hours
            )

        for (day_index, task_index), hours in sorted(merged_blocks.items()):
            task = self.tasks[task_index]
            plan.add_session(
                StudySession(
                    day=self.day_names[day_index],
                    task_title=task.title,
                    hours=round(hours, 2),
                    deadline=task.deadline,
                    priority=task.priority,
                    days_left_display=_display_days_left(
                        task,
                        day_index,
                        self.day_names,
                        self.planning_dates,
                    ),
                )
            )

        self._add_deadline_notes(plan, final_state)

        for task_index, remaining_hours in enumerate(final_state.remaining_task_hours):
            if remaining_hours > 1e-9:
                task = self.tasks[task_index]
                plan.notes.append(
                    f"Could not fully schedule '{task.title}'. "
                    f"{remaining_hours:.1f} hour(s) remain unscheduled."
                )

        if not final_state.scheduled_blocks:
            plan.notes.append("No sessions could be scheduled with the available study hours.")

        plan.notes.append(f"Planner strategy: {self.strategy.upper()} search.")
        plan.notes.append(f"Search explored {explored_states} state(s).")
        return plan

    def _add_deadline_notes(
        self,
        plan: WeeklyStudyPlan,
        final_state: PlanningState,
    ) -> None:
        """Add notes for work that misses the deadline window."""
        task_hours_before_deadline: dict[int, float] = {}
        task_hours_after_deadline: dict[int, float] = {}

        for block in final_state.scheduled_blocks:
            task = self.tasks[block.task_index]

            if is_after_deadline_slot(task, block.day_index, self.day_names, self.planning_dates):
                task_hours_after_deadline[block.task_index] = (
                    task_hours_after_deadline.get(block.task_index, 0.0) + block.hours
                )
            else:
                task_hours_before_deadline[block.task_index] = (
                    task_hours_before_deadline.get(block.task_index, 0.0) + block.hours
                )

        for task_index, task in enumerate(self.tasks):
            slot_count = deadline_slot_count(task, self.day_names, self.planning_dates)
            if slot_count is None:
                continue

            hours_before_deadline = task_hours_before_deadline.get(task_index, 0.0)
            hours_after_deadline = task_hours_after_deadline.get(task_index, 0.0)
            missed_deadline_hours = max(0.0, task.estimated_hours - hours_before_deadline)

            if missed_deadline_hours > 1e-9:
                plan.notes.append(
                    f"'{task.title}' could not be fully completed within the next {slot_count} day slot(s). "
                    f"About {missed_deadline_hours:.1f} hour(s) miss the deadline."
                )

            if hours_after_deadline > 1e-9:
                plan.notes.append(
                    f"'{task.title}' has {hours_after_deadline:.1f} hour(s) scheduled after its deadline window."
                )

    def _state_key(self, state: PlanningState) -> tuple[tuple[float, ...], tuple[float, ...]]:
        """Return a compact key for duplicate-state checking."""
        return state.remaining_task_hours, state.available_day_hours

    def _is_better_state(self, candidate: PlanningState, current_best: PlanningState) -> bool:
        """Return True when one state is better than another."""
        candidate_remaining = candidate.total_remaining_hours()
        best_remaining = current_best.total_remaining_hours()

        if candidate_remaining < best_remaining - 1e-9:
            return True
        if abs(candidate_remaining - best_remaining) <= 1e-9:
            return candidate.path_cost < current_best.path_cost
        return False


def generate_weekly_plan(
    profile: StudentProfile,
    strategy: str = "astar",
    max_states: int = 4000,
) -> WeeklyStudyPlan:
    """Generate a weekly study plan using one search strategy."""
    planner = SearchPlanner(profile=profile, strategy=strategy)
    return planner.search(max_states=max_states).weekly_plan


def compare_strategies(
    profile: StudentProfile,
    strategies: Sequence[str] = ("greedy", "astar"),
    max_states: int = 4000,
) -> list[PlanningResult]:
    """Run Greedy and A* and return their results for comparison."""
    results: list[PlanningResult] = []

    for strategy in strategies:
        planner = SearchPlanner(profile=profile, strategy=strategy)
        results.append(planner.search(max_states=max_states))

    return results


def comparison_report_lines(results: Sequence[PlanningResult]) -> list[str]:
    """Return comparison lines for coursework reporting."""
    return [result.to_summary_line() for result in results]


def _ordered_day_names_from_today(day_names: Sequence[str]) -> list[str]:
    """Rotate weekday names so the first slot is today."""
    canonical_days = list(config.DEFAULT_STUDY_DAYS)
    today_index = date.today().weekday()
    rotated = canonical_days[today_index:] + canonical_days[:today_index]

    requested_lower = {day.lower(): day for day in day_names}
    ordered_days: list[str] = []

    for canonical_day in rotated:
        if canonical_day.lower() in requested_lower:
            ordered_days.append(requested_lower[canonical_day.lower()])

    for day_name in day_names:
        if day_name not in ordered_days:
            ordered_days.append(day_name)

    return ordered_days


def _ordered_tasks(
    tasks: Sequence[Task],
    day_names: Sequence[str],
    planning_dates: Sequence[date],
) -> list[Task]:
    """Return tasks sorted so urgent and high-priority work is considered first."""
    return sorted(tasks, key=lambda task: _task_sort_key(task, day_names, planning_dates))


def _task_sort_key(
    task: Task,
    day_names: Sequence[str],
    planning_dates: Sequence[date],
) -> tuple[int, int, float]:
    """Sort by deadline urgency first, then priority, then workload."""
    return (
        deadline_rank(task, day_names, planning_dates),
        -task.priority,
        -task.estimated_hours,
    )


def _display_days_left(
    task: Task,
    day_index: int,
    day_names: Sequence[str],
    planning_dates: Sequence[date],
) -> int | None:
    """Return a display-friendly remaining days value for one session.

    This value decreases as the plan moves forward through the week. It never
    goes below zero.
    """
    starting_days_left = resolve_days_left(task, day_names, planning_dates)
    if starting_days_left is None:
        return None
    return max(0, starting_days_left - day_index)
