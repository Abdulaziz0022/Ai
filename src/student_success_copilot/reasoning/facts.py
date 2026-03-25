"""Build initial reasoning facts from a student profile."""

from __future__ import annotations

from datetime import date, datetime
from typing import TypeAlias

from student_success_copilot import config
from student_success_copilot.models.student_profile import StudentProfile
from student_success_copilot.models.task import Task


FactStrengths: TypeAlias = dict[str, float]


def build_initial_facts(profile: StudentProfile) -> FactStrengths:
    """Convert a student profile into the first set of symbolic facts."""
    facts: FactStrengths = {}

    task_count = len(profile.tasks)
    total_workload = profile.total_workload_hours()
    total_availability = profile.total_available_hours()
    high_priority_count = sum(1 for task in profile.tasks if task.priority >= 3)

    ordered_days = _ordered_day_names_from_today()
    ordered_availability = [float(profile.availability.get(day, 0.0)) for day in ordered_days]
    deadline_summary = _summarize_deadline_pressure(profile.tasks, ordered_availability)

    if task_count > 0:
        _add_fact(facts, "has_tasks", 1.0)
    if task_count >= 4:
        _add_fact(facts, "many_tasks", _scaled_confidence(task_count, 4, 6))
    if 0 < task_count <= 2:
        _add_fact(facts, "few_tasks", 0.8)

    if high_priority_count >= 1:
        _add_fact(facts, "has_high_priority_task", 0.9)
    if high_priority_count >= 2:
        _add_fact(
            facts,
            "multiple_high_priority_tasks",
            _scaled_confidence(high_priority_count, 2, 4),
        )

    if total_availability > 0:
        if total_workload > total_availability:
            overload_amount = total_workload - total_availability
            _add_fact(
                facts,
                "overloaded_schedule",
                _scaled_confidence(overload_amount, 1.0, 6.0),
            )
        if total_workload > total_availability + 3:
            _add_fact(
                facts,
                "heavy_workload_gap",
                _scaled_confidence(total_workload - total_availability, 3.0, 8.0),
            )
        if total_workload <= total_availability:
            _add_fact(facts, "balanced_workload", 0.9)
    elif total_workload > 0:
        _add_fact(facts, "no_study_time_known", 1.0)

    if total_availability < 6:
        _add_fact(
            facts,
            "limited_study_time",
            _scaled_confidence(6 - total_availability, 1.0, 6.0),
        )
    if total_availability >= 8:
        _add_fact(
            facts,
            "good_study_availability",
            _scaled_confidence(total_availability, 8.0, 16.0),
        )

    if profile.confidence is not None:
        if profile.confidence <= config.LOW_CONFIDENCE_THRESHOLD:
            _add_fact(
                facts,
                "low_confidence",
                _scaled_confidence(10 - profile.confidence, 6.0, 9.0),
            )
        elif profile.confidence <= 6:
            _add_fact(facts, "moderate_confidence", 0.7)
        else:
            _add_fact(
                facts,
                "high_confidence",
                _scaled_confidence(profile.confidence, 7.0, 10.0),
            )

    if profile.stress is not None:
        if profile.stress >= config.HIGH_STRESS_THRESHOLD:
            _add_fact(
                facts,
                "high_stress",
                _scaled_confidence(profile.stress, 8.0, 10.0),
            )
        elif profile.stress >= 6:
            _add_fact(facts, "moderate_stress", 0.7)
        else:
            _add_fact(
                facts,
                "manageable_stress",
                _scaled_confidence(10 - profile.stress, 5.0, 9.0),
            )

    if profile.attendance is not None:
        if profile.attendance < 70:
            _add_fact(
                facts,
                "poor_attendance",
                _scaled_confidence(100 - profile.attendance, 30.0, 50.0),
            )
        elif profile.attendance >= 85:
            _add_fact(
                facts,
                "strong_attendance",
                _scaled_confidence(profile.attendance, 85.0, 100.0),
            )

    if profile.quiz_score is not None:
        if profile.quiz_score < 50:
            _add_fact(
                facts,
                "poor_quiz_performance",
                _scaled_confidence(100 - profile.quiz_score, 50.0, 70.0),
            )
        elif profile.quiz_score < 70:
            _add_fact(facts, "average_quiz_performance", 0.7)
        else:
            _add_fact(
                facts,
                "strong_quiz_performance",
                _scaled_confidence(profile.quiz_score, 70.0, 95.0),
            )

    if profile.time_spent is not None:
        if profile.time_spent < 3:
            _add_fact(
                facts,
                "low_study_time",
                _scaled_confidence(6 - profile.time_spent, 2.0, 6.0),
            )
        elif profile.time_spent >= 5:
            _add_fact(
                facts,
                "steady_study_time",
                _scaled_confidence(profile.time_spent, 5.0, 10.0),
            )

    if deadline_summary["urgent_tasks"] > 0:
        _add_fact(
            facts,
            "urgent_deadline",
            _scaled_confidence(deadline_summary["urgent_tasks"], 1.0, 3.0),
        )

    if deadline_summary["near_deadline_tasks"] > 0:
        _add_fact(
            facts,
            "near_deadline",
            _scaled_confidence(deadline_summary["near_deadline_tasks"], 1.0, 4.0),
        )

    if deadline_summary["missed_hours"] > 0:
        _add_fact(
            facts,
            "after_deadline_work",
            _scaled_confidence(deadline_summary["missed_hours"], 0.5, 5.0),
        )

    if deadline_summary["missed_hours"] >= 2.0 or deadline_summary["urgent_missed_hours"] >= 1.0:
        _add_fact(
            facts,
            "severe_deadline_miss",
            _scaled_confidence(
                max(deadline_summary["missed_hours"], deadline_summary["urgent_missed_hours"]),
                1.0,
                6.0,
            ),
        )

    if deadline_summary["window_overload"] > 0:
        _add_fact(
            facts,
            "deadline_window_overload",
            _scaled_confidence(deadline_summary["window_overload"], 1.0, 6.0),
        )

    if (
        profile.confidence is not None
        and profile.quiz_score is not None
        and profile.confidence >= 8
        and profile.quiz_score < 50
    ):
        _add_fact(facts, "confidence_quiz_mismatch", 0.95)

    return facts


def _summarize_deadline_pressure(
    tasks: list[Task],
    ordered_availability: list[float],
) -> dict[str, float]:
    """Estimate missed deadline pressure from the next available day slots."""
    urgent_tasks = 0
    near_deadline_tasks = 0
    missed_hours = 0.0
    urgent_missed_hours = 0.0
    window_overload = 0.0

    resolved_tasks: list[tuple[Task, int | None]] = [
        (task, _resolve_task_days_left(task)) for task in tasks
    ]

    for task, days_left in resolved_tasks:
        if days_left is None:
            continue
        if days_left <= 1:
            urgent_tasks += 1
        if days_left <= 3:
            near_deadline_tasks += 1

        slot_count = max(0, min(len(ordered_availability), days_left))
        available_before_deadline = sum(ordered_availability[:slot_count])
        task_missed_hours = max(0.0, task.estimated_hours - available_before_deadline)
        missed_hours += task_missed_hours

        if days_left <= 1:
            urgent_missed_hours += task_missed_hours

    for window in range(1, len(ordered_availability) + 1):
        tasks_in_window = [
            task for task, days_left in resolved_tasks if days_left is not None and days_left <= window
        ]
        if not tasks_in_window:
            continue

        required_hours = sum(task.estimated_hours for task in tasks_in_window)
        available_hours = sum(ordered_availability[:window])
        window_overload = max(window_overload, required_hours - available_hours)

    return {
        "urgent_tasks": float(urgent_tasks),
        "near_deadline_tasks": float(near_deadline_tasks),
        "missed_hours": missed_hours,
        "urgent_missed_hours": urgent_missed_hours,
        "window_overload": max(0.0, window_overload),
    }


def _resolve_task_days_left(task: Task) -> int | None:
    """Resolve ``days_left`` directly from the task data."""
    if task.days_left is not None:
        return max(0, int(task.days_left))

    cleaned_deadline = task.deadline.strip()
    today = date.today()

    weekday_offsets = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    if cleaned_deadline.lower() in weekday_offsets:
        target_weekday = weekday_offsets[cleaned_deadline.lower()]
        current_weekday = today.weekday()
        return (target_weekday - current_weekday) % 7

    try:
        deadline_date = datetime.strptime(cleaned_deadline, "%Y-%m-%d").date()
    except ValueError:
        return None

    return max(0, (deadline_date - today).days)


def _ordered_day_names_from_today() -> list[str]:
    """Return weekday names rotated so the first item is today."""
    today_index = date.today().weekday()
    canonical_days = list(config.DEFAULT_STUDY_DAYS)
    return canonical_days[today_index:] + canonical_days[:today_index]


def _add_fact(facts: FactStrengths, fact_name: str, strength: float) -> None:
    """Store a fact with the strongest confidence seen so far."""
    bounded_strength = max(0.0, min(1.0, strength))
    current_strength = facts.get(fact_name, 0.0)
    if bounded_strength > current_strength:
        facts[fact_name] = bounded_strength


def _scaled_confidence(value: float, low_point: float, high_point: float) -> float:
    """Map a numeric signal into a confidence value between 0.6 and 1.0."""
    if high_point <= low_point:
        return 0.8
    ratio = (value - low_point) / (high_point - low_point)
    ratio = max(0.0, min(1.0, ratio))
    return 0.6 + (0.4 * ratio)
