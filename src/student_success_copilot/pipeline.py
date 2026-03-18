"""Basic pipeline that connects input, validation, question loop, and output."""

from __future__ import annotations

from dataclasses import dataclass, field

from student_success_copilot import config
from student_success_copilot.models.student_profile import StudentProfile
from student_success_copilot.models.study_plan import StudySession, WeeklyStudyPlan
from student_success_copilot.question_loop import run_question_loop
from student_success_copilot.validator import ValidationResult, validate_profile


@dataclass
class PipelineResult:
    """Container for the main outputs of the starter pipeline."""

    profile: StudentProfile
    validation_result: ValidationResult
    question_history: list[str] = field(default_factory=list)
    study_plan: WeeklyStudyPlan = field(default_factory=WeeklyStudyPlan)
    risk_level: str = "Medium"
    recommendations: list[str] = field(default_factory=list)
    explanation: str = ""


def run_copilot(profile: StudentProfile) -> PipelineResult:
    """Run a minimal end-to-end flow for the starter project."""
    validation_result = validate_profile(profile)
    question_history: list[str] = []

    if validation_result.has_issues:
        profile, question_history = run_question_loop(profile, validation_result)
        validation_result = validate_profile(profile)

    study_plan = create_placeholder_plan(profile)
    risk_level = estimate_placeholder_risk(profile)
    recommendations = build_placeholder_recommendations(profile, validation_result)
    explanation = generate_placeholder_explanation(
        profile=profile,
        risk_level=risk_level,
        validation_result=validation_result,
        recommendations=recommendations,
    )

    return PipelineResult(
        profile=profile,
        validation_result=validation_result,
        question_history=question_history,
        study_plan=study_plan,
        risk_level=risk_level,
        recommendations=recommendations,
        explanation=explanation,
    )


def create_placeholder_plan(profile: StudentProfile) -> WeeklyStudyPlan:
    """Create a simple study plan without full search-based planning yet."""
    plan = WeeklyStudyPlan()
    remaining_hours = dict(profile.availability)

    if not remaining_hours:
        remaining_hours = {"Monday": 2.0}

    if not profile.tasks:
        first_day = next(iter(remaining_hours))
        plan.add_session(
            StudySession(
                day=first_day,
                task_title="General revision",
                hours=1.0,
                notes="Placeholder session because no tasks were provided.",
            )
        )
        return plan

    days = list(remaining_hours.keys())

    for task in profile.tasks:
        hours_left = max(task.estimated_hours, 1.0)

        for day in days:
            free_hours = remaining_hours.get(day, 0.0)
            if free_hours <= 0:
                continue

            planned_hours = min(
                free_hours,
                hours_left,
                config.DEFAULT_SESSION_LENGTH_HOURS,
            )

            plan.add_session(
                StudySession(
                    day=day,
                    task_title=task.title,
                    hours=planned_hours,
                    notes=f"Target deadline: {task.deadline}",
                )
            )

            remaining_hours[day] -= planned_hours
            hours_left -= planned_hours

            if hours_left <= 0:
                break

        if hours_left > 0:
            plan.notes.append(
                f"Not enough free time to fully schedule '{task.title}'. "
                f"{hours_left:.1f} hour(s) remain unscheduled."
            )

    if not plan.notes:
        plan.notes.append(
            "This is a starter schedule using simple placeholder logic."
        )

    return plan


def estimate_placeholder_risk(profile: StudentProfile) -> str:
    """Estimate a simple risk label using beginner-friendly placeholder rules."""
    score = 0
    total_workload = profile.total_workload_hours()
    total_availability = profile.total_available_hours()

    if profile.stress is not None:
        if profile.stress >= 8:
            score += 2
        elif profile.stress >= 6:
            score += 1

    if profile.confidence is not None:
        if profile.confidence <= 4:
            score += 2
        elif profile.confidence <= 6:
            score += 1

    if total_workload > total_availability + 2:
        score += 2
    elif total_workload > total_availability:
        score += 1

    if profile.quiz_score is not None:
        if profile.quiz_score < 50:
            score += 2
        elif profile.quiz_score < 70:
            score += 1

    if profile.attendance is not None and profile.attendance < 70:
        score += 1

    if score >= 5:
        return "High"
    if score >= 3:
        return "Medium"
    return "Low"


def build_placeholder_recommendations(
    profile: StudentProfile,
    validation_result: ValidationResult,
) -> list[str]:
    """Generate simple recommendations until the real AI modules are added."""
    recommendations: list[str] = []

    if validation_result.missing_fields:
        recommendations.append("Fill in any remaining missing study information.")

    if profile.total_workload_hours() > profile.total_available_hours():
        recommendations.append(
            "Your workload is higher than your free time. Reduce scope or add study hours."
        )

    if profile.stress is not None and profile.stress >= config.HIGH_STRESS_THRESHOLD:
        recommendations.append(
            "Plan shorter study blocks and include short breaks to manage stress."
        )

    if profile.confidence is not None and profile.confidence <= config.LOW_CONFIDENCE_THRESHOLD:
        recommendations.append(
            "Start with easier topics first to rebuild confidence."
        )

    if profile.quiz_score is not None and profile.quiz_score < 60:
        recommendations.append(
            "Add a revision session focused on weak quiz topics."
        )

    if not recommendations:
        recommendations.append(
            "Keep following a steady study routine and review progress each week."
        )

    return recommendations


def generate_placeholder_explanation(
    profile: StudentProfile,
    risk_level: str,
    validation_result: ValidationResult,
    recommendations: list[str],
) -> str:
    """Create a short explanation for the starter version."""
    parts = [
        f"The current risk level is {risk_level}.",
        (
            f"You have {len(profile.tasks)} task(s), "
            f"{profile.total_workload_hours():.1f} estimated workload hour(s), and "
            f"{profile.total_available_hours():.1f} available study hour(s)."
        ),
    ]

    if validation_result.contradictions:
        parts.append(
            "Some answers looked inconsistent, so the system asked follow-up questions."
        )

    parts.append(
        "These recommendations come from simple placeholder checks and will later be "
        "replaced by search, rule-based reasoning, and machine learning components."
    )
    parts.append(f"Top recommendation: {recommendations[0]}")

    return " ".join(parts)
