"""Build initial reasoning facts from a student profile.

This module converts the raw ``StudentProfile`` data into a small set of
explainable symbolic facts. Each fact is stored with a confidence value between
0.0 and 1.0 so later reasoning stages can keep track of how strongly a
conclusion is supported.
"""

from __future__ import annotations

from typing import TypeAlias

from student_success_copilot import config
from student_success_copilot.models.student_profile import StudentProfile


FactStrengths: TypeAlias = dict[str, float]


def build_initial_facts(profile: StudentProfile) -> FactStrengths:
    """Convert a student profile into the first set of symbolic facts.

    The facts are intentionally simple and coursework-friendly. Most of them
    come directly from thresholds so that the system stays explainable.
    """
    facts: FactStrengths = {}

    task_count = len(profile.tasks)
    total_workload = profile.total_workload_hours()
    total_availability = profile.total_available_hours()
    high_priority_count = sum(1 for task in profile.tasks if task.priority >= 3)

    if task_count > 0:
        _add_fact(facts, "has_tasks", 1.0)
    if task_count >= 4:
        _add_fact(facts, "many_tasks", _scaled_confidence(task_count, 4, 6))
    if task_count <= 2 and task_count > 0:
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

    if (
        profile.confidence is not None
        and profile.quiz_score is not None
        and profile.confidence >= 8
        and profile.quiz_score < 50
    ):
        _add_fact(facts, "confidence_quiz_mismatch", 0.95)

    return facts


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
