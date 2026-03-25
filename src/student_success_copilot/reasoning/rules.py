"""Rule definitions for the Student Success Copilot reasoning layer."""

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
        name="R1_low_confidence_and_high_stress",
        premises=("low_confidence", "high_stress"),
        conclusion="high_risk",
        strength=0.96,
        description="Low confidence and very high stress strongly suggest high risk.",
        category="risk",
    ),
    Rule(
        name="R2_urgent_deadline_and_overload",
        premises=("urgent_deadline", "overloaded_schedule"),
        conclusion="high_risk",
        strength=0.95,
        description="An urgent deadline plus overall overload suggests high risk.",
        category="risk",
    ),
    Rule(
        name="R3_severe_deadline_miss",
        premises=("severe_deadline_miss",),
        conclusion="high_risk",
        strength=0.97,
        description="A severe missed-deadline situation directly suggests high risk.",
        category="risk",
    ),
    Rule(
        name="R4_after_deadline_work_and_high_stress",
        premises=("after_deadline_work", "high_stress"),
        conclusion="high_risk",
        strength=0.94,
        description="Work slipping past a deadline under high stress suggests high risk.",
        category="risk",
    ),
    Rule(
        name="R5_deadline_window_overload_and_urgent",
        premises=("deadline_window_overload", "urgent_deadline"),
        conclusion="high_risk",
        strength=0.95,
        description="Too much work inside a very short deadline window suggests high risk.",
        category="risk",
    ),
    Rule(
        name="R6_high_stress_and_overload",
        premises=("high_stress", "overloaded_schedule"),
        conclusion="high_risk",
        strength=0.93,
        description="High stress combined with overload suggests high risk.",
        category="risk",
    ),
    Rule(
        name="R7_low_confidence_and_poor_quiz",
        premises=("low_confidence", "poor_quiz_performance"),
        conclusion="high_risk",
        strength=0.92,
        description="Low confidence and poor quiz performance suggest high risk.",
        category="risk",
    ),
    Rule(
        name="R8_multiple_priority_tasks_and_gap",
        premises=("multiple_high_priority_tasks", "heavy_workload_gap"),
        conclusion="high_risk",
        strength=0.9,
        description="Several high-priority tasks plus a large workload gap suggest high risk.",
        category="risk",
    ),
    Rule(
        name="R9_after_deadline_work_and_low_confidence",
        premises=("after_deadline_work", "low_confidence"),
        conclusion="high_risk",
        strength=0.9,
        description="Missing deadline time while confidence is low suggests high risk.",
        category="risk",
    ),
    Rule(
        name="R10_many_tasks_and_limited_time",
        premises=("many_tasks", "limited_study_time"),
        conclusion="medium_risk",
        strength=0.82,
        description="Many tasks and little study time suggest medium risk.",
        category="risk",
    ),
    Rule(
        name="R11_poor_attendance_and_poor_quiz",
        premises=("poor_attendance", "poor_quiz_performance"),
        conclusion="medium_risk",
        strength=0.85,
        description="Poor attendance plus poor quiz performance suggest medium risk.",
        category="risk",
    ),
    Rule(
        name="R12_moderate_stress_and_average_quiz",
        premises=("moderate_stress", "average_quiz_performance"),
        conclusion="medium_risk",
        strength=0.78,
        description="Moderate stress with average quiz performance suggests medium risk.",
        category="risk",
    ),
    Rule(
        name="R13_moderate_stress_and_moderate_confidence",
        premises=("moderate_stress", "moderate_confidence"),
        conclusion="medium_risk",
        strength=0.76,
        description="Moderate stress with only moderate confidence suggests medium risk.",
        category="risk",
    ),
    Rule(
        name="R14_low_confidence_and_overload",
        premises=("low_confidence", "overloaded_schedule"),
        conclusion="medium_risk",
        strength=0.84,
        description="Low confidence and an overloaded schedule suggest medium risk.",
        category="risk",
    ),
    Rule(
        name="R15_has_tasks_and_limited_time",
        premises=("has_tasks", "limited_study_time"),
        conclusion="medium_risk",
        strength=0.72,
        description="Having tasks but limited study time suggests medium risk.",
        category="risk",
    ),
    Rule(
        name="R16_near_deadline_and_window_overload",
        premises=("near_deadline", "deadline_window_overload"),
        conclusion="medium_risk",
        strength=0.84,
        description="A near deadline with too much work in the short term suggests medium risk.",
        category="risk",
    ),
    Rule(
        name="R17_balanced_workload_good_progress",
        premises=("balanced_workload", "manageable_stress", "high_confidence"),
        conclusion="low_risk",
        strength=0.88,
        description="Balanced workload, manageable stress, and high confidence suggest low risk.",
        category="risk",
    ),
    Rule(
        name="R18_strong_attendance_and_quiz",
        premises=("strong_attendance", "strong_quiz_performance"),
        conclusion="low_risk",
        strength=0.84,
        description="Strong attendance and strong quiz results suggest low risk.",
        category="risk",
    ),
    Rule(
        name="R19_balanced_and_steady",
        premises=("balanced_workload", "steady_study_time"),
        conclusion="low_risk",
        strength=0.74,
        description="A balanced workload and steady study time suggest low risk.",
        category="risk",
    ),
    Rule(
        name="R20_low_confidence_support",
        premises=("low_confidence",),
        conclusion="recommend_start_easy_topics",
        strength=0.9,
        description="Low confidence suggests starting with easier topics.",
        recommendation="Start with easier topics first, then move to harder work.",
        category="recommendation",
    ),
    Rule(
        name="R21_poor_quiz_support",
        premises=("poor_quiz_performance",),
        conclusion="recommend_revision_sessions",
        strength=0.92,
        description="Poor quiz performance suggests targeted revision sessions.",
        recommendation="Schedule revision sessions for the topics where quiz performance was weakest.",
        category="recommendation",
    ),
    Rule(
        name="R22_high_stress_support",
        premises=("high_stress",),
        conclusion="recommend_short_study_blocks",
        strength=0.88,
        description="High stress suggests shorter study blocks and breaks.",
        recommendation="Use shorter study blocks and add short breaks to reduce pressure.",
        category="recommendation",
    ),
    Rule(
        name="R23_after_deadline_support",
        premises=("after_deadline_work",),
        conclusion="recommend_focus_urgent_task",
        strength=0.94,
        description="Deadline slippage suggests focusing on the most urgent task first.",
        recommendation="Focus on the most urgent deadline first and reduce less urgent work this week.",
        category="recommendation",
    ),
    Rule(
        name="R24_severe_deadline_miss_support",
        premises=("severe_deadline_miss",),
        conclusion="recommend_seek_support",
        strength=0.95,
        description="A severe missed-deadline case suggests asking for support early.",
        recommendation="Ask for support early because the current workload may not fit before the deadline.",
        category="recommendation",
    ),
    Rule(
        name="R25_has_tasks_support",
        premises=("has_tasks",),
        conclusion="recommend_follow_plan",
        strength=0.68,
        description="Any student with tasks should follow a clear weekly plan.",
        recommendation="Follow the weekly study plan and tick off progress after each session.",
        category="recommendation",
    ),
]


def get_rules() -> list[Rule]:
    """Return a copy of the rule list for callers that want to modify it safely."""
    return list(RULES)
