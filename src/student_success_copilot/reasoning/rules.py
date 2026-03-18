"""Rule definitions for the coursework reasoning layer."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Rule:
    """Represent one explainable IF-THEN rule."""

    name: str
    premises: tuple[str, ...]
    conclusion: str
    strength: float = 1.0
    description: str = ""
    recommendation: str | None = None
    category: str = "general"
    metadata: dict[str, str] = field(default_factory=dict)


RULES: list[Rule] = [
    Rule(
        name="R1_high_stress_and_overload",
        premises=("high_stress", "overloaded_schedule"),
        conclusion="high_risk",
        strength=0.95,
        description="A student with high stress and more work than available time is at high risk.",
        category="risk",
    ),
    Rule(
        name="R2_low_confidence_and_poor_quiz",
        premises=("low_confidence", "poor_quiz_performance"),
        conclusion="high_risk",
        strength=0.92,
        description="Low confidence combined with weak quiz results suggests a high academic risk.",
        category="risk",
    ),
    Rule(
        name="R3_poor_attendance_and_poor_quiz",
        premises=("poor_attendance", "poor_quiz_performance"),
        conclusion="medium_risk",
        strength=0.85,
        description="Low attendance plus poor quiz performance suggests medium risk.",
        category="risk",
    ),
    Rule(
        name="R4_many_tasks_and_limited_time",
        premises=("many_tasks", "limited_study_time"),
        conclusion="medium_risk",
        strength=0.82,
        description="Many tasks with little available study time increase risk.",
        category="risk",
    ),
    Rule(
        name="R5_multiple_priority_tasks_and_overload",
        premises=("multiple_high_priority_tasks", "overloaded_schedule"),
        conclusion="high_risk",
        strength=0.9,
        description="Several high-priority tasks and an overloaded schedule make high risk likely.",
        category="risk",
    ),
    Rule(
        name="R6_moderate_risk_and_high_stress",
        premises=("medium_risk", "high_stress"),
        conclusion="high_risk",
        strength=0.8,
        description="Medium risk becomes high risk when stress is already very high.",
        category="risk",
    ),
    Rule(
        name="R7_balanced_workload_good_progress",
        premises=("balanced_workload", "manageable_stress", "high_confidence"),
        conclusion="low_risk",
        strength=0.88,
        description="Balanced workload, manageable stress, and high confidence indicate low risk.",
        category="risk",
    ),
    Rule(
        name="R8_good_attendance_and_good_quiz",
        premises=("strong_attendance", "strong_quiz_performance"),
        conclusion="low_risk",
        strength=0.84,
        description="Strong attendance and good quiz performance support a low-risk judgement.",
        category="risk",
    ),
    Rule(
        name="R9_low_confidence_support",
        premises=("low_confidence",),
        conclusion="recommend_start_easy_topics",
        strength=0.9,
        description="Students with low confidence should begin with easier topics to rebuild momentum.",
        recommendation="Start with easier topics first, then move to harder work.",
        category="recommendation",
    ),
    Rule(
        name="R10_poor_quiz_support",
        premises=("poor_quiz_performance",),
        conclusion="recommend_revision_sessions",
        strength=0.92,
        description="Weak quiz performance suggests targeted revision sessions are needed.",
        recommendation="Schedule revision sessions for the topics where quiz performance was weakest.",
        category="recommendation",
    ),
    Rule(
        name="R11_high_stress_support",
        premises=("high_stress",),
        conclusion="recommend_short_study_blocks",
        strength=0.88,
        description="High stress suggests shorter sessions with breaks.",
        recommendation="Use shorter study blocks and add short breaks to reduce pressure.",
        category="recommendation",
    ),
    Rule(
        name="R12_poor_attendance_support",
        premises=("poor_attendance",),
        conclusion="recommend_review_missed_material",
        strength=0.86,
        description="Low attendance suggests the student should review missed material.",
        recommendation="Review missed classes or lecture notes before attempting new tasks.",
        category="recommendation",
    ),
    Rule(
        name="R13_low_time_many_tasks_support",
        premises=("low_study_time", "many_tasks"),
        conclusion="recommend_increase_study_time",
        strength=0.84,
        description="Low study time and many tasks suggest the student should increase planned study hours.",
        recommendation="Increase study time this week or reduce the amount of work planned.",
        category="recommendation",
    ),
    Rule(
        name="R14_workload_gap_support",
        premises=("heavy_workload_gap",),
        conclusion="recommend_reduce_scope",
        strength=0.9,
        description="A large gap between workload and available time suggests reducing scope or seeking support.",
        recommendation="Reduce scope, ask for help, or spread tasks over more days.",
        category="recommendation",
    ),
    Rule(
        name="R15_confidence_quiz_mismatch_check",
        premises=("confidence_quiz_mismatch",),
        conclusion="recommend_check_understanding",
        strength=0.78,
        description="A mismatch between very high confidence and weak quiz results suggests a misunderstanding.",
        recommendation="Double-check understanding with practice questions or feedback from a tutor.",
        category="recommendation",
    ),
]


def get_rules() -> list[Rule]:
    """Return a copy of the rule list for callers that want to modify it safely."""
    return list(RULES)
