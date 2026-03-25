"""Explanation helpers for the integrated Student Success Copilot app."""

from __future__ import annotations

from typing import Sequence

from student_success_copilot.models.student_profile import StudentProfile
from student_success_copilot.models.study_plan import WeeklyStudyPlan
from student_success_copilot.planning.search_planner import PlanningResult
from student_success_copilot.reasoning.forward_chain import ForwardChainingResult
from student_success_copilot.risk_assessor import RiskAssessmentResult
from student_success_copilot.validator import ValidationResult


def summarize_reasoning_trace(
    reasoning_result: ForwardChainingResult,
    limit: int = 5,
) -> list[str]:
    """Return short trace lines for the CLI."""
    lines: list[str] = []

    for step in reasoning_result.trace[:limit]:
        lines.append(
            f"{step.rule_name}: {', '.join(step.premises)} -> {step.conclusion} "
            f"(strength {step.conclusion_strength:.2f})"
        )

    if not lines:
        lines.append("No rules fired during forward chaining.")

    return lines


def summarize_planning_results(planning_results: Sequence[PlanningResult]) -> list[str]:
    """Return planning comparison lines that fit nicely in the terminal."""
    if not planning_results:
        return ["No planning results were available."]
    return [result.to_summary_line() for result in planning_results]


def generate_final_explanation(
    profile: StudentProfile,
    validation_result: ValidationResult,
    question_history: Sequence[str],
    risk_assessment: RiskAssessmentResult,
    study_plan: WeeklyStudyPlan,
    recommendations: Sequence[str],
    planning_summary: Sequence[str],
) -> str:
    """Create one clear paragraph-style explanation for the final output."""
    parts = [
        (
            f"The final risk level is {risk_assessment.final_risk}. "
            f"Rule-based reasoning suggested {risk_assessment.rule_risk}"
            + (
                f", and the ML model suggested {risk_assessment.ml_risk}."
                if risk_assessment.ml_risk
                else "."
            )
        ),
        (
            f"You currently have {len(profile.tasks)} task(s), "
            f"{profile.total_workload_hours():.1f} workload hour(s), and "
            f"{profile.total_available_hours():.1f} available study hour(s)."
        ),
    ]

    if risk_assessment.disagreement_note:
        parts.append(risk_assessment.disagreement_note)

    if risk_assessment.reasons:
        parts.append(f"Main rule-based reason: {risk_assessment.reasons[0]}")

    if question_history:
        parts.append(
            "The follow-up question loop changed the result by filling in missing or conflicting information before reasoning and planning."
        )

    if validation_result.warnings:
        parts.append(f"Validation warning: {validation_result.warnings[0]}")

    if recommendations:
        parts.append(f"Top recommendation: {recommendations[0]}")

    if study_plan.sessions:
        parts.append(
            f"The study plan created {len(study_plan.sessions)} session(s) for the week."
        )
    else:
        parts.append("No study sessions could be created from the current inputs.")

    if planning_summary:
        parts.append(f"Planning comparison: {planning_summary[0]}")

    return " ".join(parts)
