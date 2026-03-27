"""Main orchestration pipeline for Student Success Copilot."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from student_success_copilot.explainer import (
    generate_final_explanation,
    summarize_planning_results,
    summarize_reasoning_trace,
)
from student_success_copilot.models.student_profile import StudentProfile
from student_success_copilot.models.study_plan import WeeklyStudyPlan
from student_success_copilot.planning.search_planner import (
    PlanningResult,
    compare_strategies,
)
from student_success_copilot.planning.state import PlanningState
from student_success_copilot.question_loop import run_question_loop
from student_success_copilot.reasoning.facts import FactStrengths, build_initial_facts
from student_success_copilot.reasoning.forward_chain import (
    ForwardChainingResult,
    forward_chain,
)
from student_success_copilot.risk_assessor import RiskAssessmentResult, assess_risk
from student_success_copilot.validator import ValidationResult, validate_profile

if TYPE_CHECKING:
    from student_success_copilot.ml.evaluate import EvaluationResult
    from student_success_copilot.ml.predict import PredictionResult
    from student_success_copilot.ml.train import TrainedRiskModel


@dataclass
class PipelineResult:
    """Container for the main outputs of the integrated pipeline."""

    profile: StudentProfile
    validation_result: ValidationResult
    question_history: list[str] = field(default_factory=list)
    study_plan: WeeklyStudyPlan = field(default_factory=WeeklyStudyPlan)
    risk_level: str = "Medium"
    rule_risk_level: str = "Medium"
    ml_risk_level: str | None = None
    recommendations: list[str] = field(default_factory=list)
    explanation: str = ""
    reasoning_trace: list[str] = field(default_factory=list)
    proof_summary: list[str] = field(default_factory=list)
    planning_summary: list[str] = field(default_factory=list)
    risk_reasons: list[str] = field(default_factory=list)
    disagreement_note: str = ""
    ml_summary: list[str] = field(default_factory=list)


def run_copilot(profile: StudentProfile) -> PipelineResult:
    """Run the full coursework-friendly workflow."""
    validation_result = validate_profile(profile)
    question_history: list[str] = []

    if validation_result.has_issues:
        profile, question_history = run_question_loop(profile, validation_result)
        validation_result = validate_profile(profile)

    initial_facts = build_initial_facts(profile)
    reasoning_result = forward_chain(initial_facts)

    planning_results = _build_plans(profile)
    selected_plan_result = _choose_plan_result(planning_results)
    planning_summary = summarize_planning_results(planning_results)

    ml_prediction, ml_summary = _run_ml_prediction(profile)
    risk_assessment = assess_risk(initial_facts, reasoning_result, ml_prediction)

    recommendations = _build_recommendations(reasoning_result, risk_assessment)
    reasoning_trace = summarize_reasoning_trace(reasoning_result)
    proof_summary = list(risk_assessment.proof_summary)

    explanation = generate_final_explanation(
        profile=profile,
        validation_result=validation_result,
        question_history=question_history,
        risk_assessment=risk_assessment,
        study_plan=selected_plan_result.weekly_plan,
        recommendations=recommendations,
        planning_summary=planning_summary,
    )

    return PipelineResult(
        profile=profile,
        validation_result=validation_result,
        question_history=question_history,
        study_plan=selected_plan_result.weekly_plan,
        risk_level=risk_assessment.final_risk,
        rule_risk_level=risk_assessment.rule_risk,
        ml_risk_level=risk_assessment.ml_risk,
        recommendations=recommendations,
        explanation=explanation,
        reasoning_trace=reasoning_trace,
        proof_summary=proof_summary,
        planning_summary=planning_summary,
        risk_reasons=list(risk_assessment.reasons),
        disagreement_note=risk_assessment.disagreement_note,
        ml_summary=ml_summary,
    )


def _build_plans(profile: StudentProfile) -> list[PlanningResult]:
    """Run the search planner strategies and fall back safely if needed."""
    try:
        return compare_strategies(profile)
    except Exception as error:  # no cover - defensive fallback
        fallback_plan = WeeklyStudyPlan()
        fallback_plan.notes.append(f"Planning fallback used because of an error: {error}")
        fallback_state = PlanningState(
            remaining_task_hours=tuple(),
            available_day_hours=tuple(),
        )
        return [
            PlanningResult(
                strategy="astar",
                final_state=fallback_state,
                weekly_plan=fallback_plan,
                explored_states=0,
                goal_reached=False,
            )
        ]


def _choose_plan_result(planning_results: list[PlanningResult]) -> PlanningResult:
    """Prefer A* when available, otherwise use the first available result."""
    for result in planning_results:
        if result.strategy.lower() == "astar":
            return result
    return planning_results[0]


def _run_ml_prediction(profile: StudentProfile) -> tuple[Any | None, list[str]]:
    """Train the ML model, evaluate it, and predict risk for one student."""
    summary: list[str] = []

    try:
        from student_success_copilot.ml.evaluate import evaluate_model
        from student_success_copilot.ml.predict import predict_risk
        from student_success_copilot.ml.train import train_risk_model

        trained_model = train_risk_model()
        evaluation = evaluate_model(trained_model)
        prediction = predict_risk(trained_model, profile)
    except Exception as error:  # pragma: no cover - defensive fallback
        summary.append(
            "ML prediction unavailable, so the final decision fell back to rule-based reasoning."
        )
        summary.append(f"Training or prediction error: {error}")
        return None, summary

    summary.extend(_build_ml_summary(prediction, trained_model, evaluation))
    return prediction, summary


def _build_ml_summary(
    prediction: "PredictionResult",
    trained_model: "TrainedRiskModel",
    evaluation: "EvaluationResult",
) -> list[str]:
    """Create short ML summary lines for the CLI."""
    probability_text = ", ".join(
        f"{label} {probability:.2f}"
        for label, probability in prediction.probabilities.items()
    )

    return [
        "ML model: logistic regression trained on historical_students.csv.",
        f"ML prediction for this student: {prediction.predicted_risk}.",
        f"Prediction probabilities: {probability_text or 'Not available.'}",
        (
            "Model evaluation on the held-out test set: "
            f"accuracy {evaluation.accuracy:.2f}, precision {evaluation.precision:.2f}, "
            f"recall {evaluation.recall:.2f}, F1 {evaluation.f1_score:.2f}."
        ),
        f"Training examples used: {len(trained_model.X_train) + len(trained_model.X_test)}.",
    ]


def _build_recommendations(
    reasoning_result: ForwardChainingResult,
    risk_assessment: RiskAssessmentResult,
) -> list[str]:
    """Merge recommendation facts with a small fallback recommendation."""
    recommendations = reasoning_result.get_recommendations()

    if risk_assessment.final_risk == "High":
        recommendations.append(
            "Check your most urgent tasks first and ask for support early if the workload still feels too high."
        )
    elif risk_assessment.final_risk == "Medium":
        recommendations.append(
            "Review progress mid-week so you can adjust the plan before deadlines become urgent."
        )

    if not recommendations:
        recommendations.append(
            "Keep following the weekly plan and review your progress at the end of the week."
        )

    return _unique(recommendations)


def _unique(items: list[str]) -> list[str]:
    """Return items in order without duplicates."""
    seen: set[str] = set()
    ordered: list[str] = []

    for item in items:
        if item not in seen:
            ordered.append(item)
            seen.add(item)

    return ordered
