"""Search-based planner for building a weekly study plan."""

from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count
from typing import Sequence

from student_success_copilot import config
from student_success_copilot.models.student_profile import StudentProfile
from student_success_copilot.models.study_plan import StudySession, WeeklyStudyPlan
from student_success_copilot.models.task import Task
from student_success_copilot.planning.heuristics import action_cost, planning_heuristic
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
        self.day_names = list(day_names or config.DEFAULT_STUDY_DAYS)
        self.tasks = _ordered_tasks(profile.tasks, self.day_names)
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
            key=lambda index: _task_sort_key(self.tasks[index], self.day_names),
        )

        day_indices = [index for index, hours in enumerate(state.available_day_hours) if hours > 1e-9]
        actions: list[PlanningAction] = []

        for task_index in task_indices:
            remaining_task_hours = state.remaining_task_hours[task_index]

            for day_index in day_indices:
                free_day_hours = state.available_day_hours[day_index]
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
                _task_sort_key(self.tasks[action.task_index], self.day_names),
                action.day_index,
                -action.hours,
            )
        )
        return actions

    def is_goal_state(self, state: PlanningState) -> bool:
        """Return True when all task hours are scheduled."""
        return state.is_goal()

    def heuristic(self, state: PlanningState) -> float:
        """Return the heuristic estimate for the current state."""
        return planning_heuristic(state, self.tasks, self.day_names)

    def step_cost(self, action: PlanningAction) -> float:
        """Return the path-cost added by a single action."""
        task = self.tasks[action.task_index]
        return action_cost(task, action.day_index, action.hours, self.day_names)

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
        heappush(frontier, (self.evaluate_priority(initial_state), next(self._state_counter), initial_state))

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
                    notes=f"Deadline: {task.deadline}; priority {task.priority}",
                )
            )

        for task_index, remaining_hours in enumerate(final_state.remaining_task_hours):
            if remaining_hours > 1e-9:
                task = self.tasks[task_index]
                plan.notes.append(
                    f"Could not fully schedule '{task.title}'. "
                    f"{remaining_hours:.1f} hour(s) remain unscheduled."
                )

        if not final_state.scheduled_blocks:
            plan.notes.append("No sessions could be scheduled with the available study hours.")

        plan.notes.append(
            f"Planner strategy: {self.strategy.upper()} search."
        )
        plan.notes.append(
            f"Search explored {explored_states} state(s)."
        )

        return plan

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
    """Run both search strategies and return their results for comparison."""
    results: list[PlanningResult] = []

    for strategy in strategies:
        planner = SearchPlanner(profile=profile, strategy=strategy)
        results.append(planner.search(max_states=max_states))

    return results


def comparison_report_lines(results: Sequence[PlanningResult]) -> list[str]:
    """Return simple comparison lines that can be copied into a coursework report."""
    return [result.to_summary_line() for result in results]


def _ordered_tasks(tasks: Sequence[Task], day_names: Sequence[str]) -> list[Task]:
    """Return tasks sorted so urgent and high-priority work is considered first."""
    return sorted(tasks, key=lambda task: _task_sort_key(task, day_names))


def _task_sort_key(task: Task, day_names: Sequence[str]) -> tuple[int, int, float]:
    """Sort by deadline urgency first, then by priority, then by workload."""
    from student_success_copilot.planning.heuristics import deadline_rank

    return (
        deadline_rank(task.deadline, day_names),
        -task.priority,
        -task.estimated_hours,
    )
