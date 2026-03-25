"""Combine rule-based reasoning and ML prediction into one final risk result."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from student_success_copilot.reasoning.backward_chain import (
    BackwardChainingResult,
    backward_chain,
)
from student_success_copilot.reasoning.forward_chain import ForwardChainingResult


RISK_SCORES = {"Low": 1, "Medium": 2, "High": 3}
MINIMUM_STRONG_PROOF = 0.6


@dataclass
class RiskAssessmentResult:
    """Store the merged risk judgement and supporting details."""

    final_risk: str
    rule_risk: str
    rule_strength: float
    ml_risk: str | None = None
    ml_probabilities: dict[str, float] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    disagreement_note: str = ""
    proof_summary: list[str] = field(default_factory=list)


def assess_risk(
    initial_facts: Mapping[str, float],
    reasoning_result: ForwardChainingResult,
    ml_prediction: Any | None = None,
) -> RiskAssessmentResult:
    """Merge symbolic reasoning and ML prediction into one final label."""
    proofs = {
        "High": backward_chain("high_risk", initial_facts),
        "Medium": backward_chain("medium_risk", initial_facts),
        "Low": backward_chain("low_risk", initial_facts),
    }

    rule_risk, rule_strength = _choose_rule_risk(proofs, reasoning_result)
    reasons = _build_reasons(reasoning_result, rule_risk)
    proof_summary = _build_proof_summary(rule_risk, proofs, reasoning_result)

    if ml_prediction is None:
        return RiskAssessmentResult(
            final_risk=rule_risk,
            rule_risk=rule_risk,
            rule_strength=rule_strength,
            reasons=reasons,
            disagreement_note=(
                "The final risk came from rule-based reasoning because the ML model was not available."
            ),
            proof_summary=proof_summary,
        )

    ml_risk = str(getattr(ml_prediction, "predicted_risk", "Medium"))
    ml_probabilities = dict(getattr(ml_prediction, "probabilities", {}))

    if ml_risk == rule_risk:
        final_risk = rule_risk
        disagreement_note = "Rules and ML agreed on the same risk level."
    elif rule_strength >= 0.75:
        final_risk = rule_risk
        disagreement_note = (
            "Rules and ML disagreed, but the rule-based proof was strong enough to keep the rule result."
        )
    else:
        final_risk = _label_from_score(max(RISK_SCORES[rule_risk], RISK_SCORES.get(ml_risk, 2)))
        disagreement_note = (
            "Rules and ML disagreed, so the system chose the more cautious higher risk level."
        )

    return RiskAssessmentResult(
        final_risk=final_risk,
        rule_risk=rule_risk,
        rule_strength=rule_strength,
        ml_risk=ml_risk,
        ml_probabilities=ml_probabilities,
        reasons=reasons,
        disagreement_note=disagreement_note,
        proof_summary=proof_summary,
    )


def _choose_rule_risk(
    proofs: dict[str, BackwardChainingResult],
    reasoning_result: ForwardChainingResult,
) -> tuple[str, float]:
    """Choose the symbolic risk label with a cautious preference order."""
    if proofs["High"].proved:
        return "High", proofs["High"].strength
    if proofs["Medium"].proved:
        return "Medium", proofs["Medium"].strength
    if proofs["Low"].proved:
        return "Low", proofs["Low"].strength

    if "high_risk" in reasoning_result.facts:
        return "High", reasoning_result.facts["high_risk"]
    if "medium_risk" in reasoning_result.facts:
        return "Medium", reasoning_result.facts["medium_risk"]
    if "low_risk" in reasoning_result.facts:
        return "Low", reasoning_result.facts["low_risk"]

    return "Medium", 0.0


def _build_reasons(
    reasoning_result: ForwardChainingResult,
    rule_risk: str,
) -> list[str]:
    """Turn the chosen rule label into short human-readable reasons."""
    target_fact = f"{rule_risk.lower()}_risk"
    reasons: list[str] = []

    for step in reasoning_result.trace:
        if step.conclusion == target_fact:
            reasons.append(
                f"{step.rule_name} fired: {', '.join(step.premises)} -> {step.conclusion} "
                f"(strength {step.conclusion_strength:.2f})."
            )

    if reasons:
        return reasons

    supporting_steps = _matching_trace_steps(reasoning_result, target_fact)
    for step in supporting_steps[:3]:
        reasons.append(
            f"{step.rule_name} added {step.conclusion} with strength {step.conclusion_strength:.2f}."
        )

    if not reasons:
        reasons.append(
            "No specific risk rule fired, so the rule-based layer kept a cautious medium default."
        )

    return reasons


def _build_proof_summary(
    rule_risk: str,
    proofs: dict[str, BackwardChainingResult],
    reasoning_result: ForwardChainingResult,
) -> list[str]:
    """Create a proof summary for the chosen symbolic risk label.

    If backward chaining cannot provide a strong proof, the summary falls back
    to the forward-chaining trace for the chosen rule label.
    """
    chosen_proof = proofs[rule_risk]

    if chosen_proof.proved and chosen_proof.strength >= MINIMUM_STRONG_PROOF:
        return _format_backward_proof(chosen_proof)

    target_fact = f"{rule_risk.lower()}_risk"
    forward_summary = _format_forward_support(reasoning_result, target_fact)
    if forward_summary:
        return forward_summary

    return _format_backward_proof(chosen_proof)


def _format_backward_proof(proof: BackwardChainingResult) -> list[str]:
    """Convert a backward-chaining proof into short display lines."""
    summary: list[str] = []

    for step in proof.proof_path[:5]:
        marker = "proved" if step.success else "failed"
        summary.append(
            f"{step.goal}: {marker} ({step.strength:.2f}) - {step.detail}"
        )

    if not summary:
        summary.append(f"No proof steps were recorded for the {proof.goal} conclusion.")

    return summary


def _format_forward_support(
    reasoning_result: ForwardChainingResult,
    target_fact: str,
) -> list[str]:
    """Build a fallback summary from the forward-chaining trace."""
    matching_steps = _matching_trace_steps(reasoning_result, target_fact)
    if not matching_steps:
        return []

    summary = [
        "Backward chaining was weak for this label, so the system used forward-chaining evidence instead."
    ]

    for step in matching_steps[:4]:
        summary.append(
            f"{step.rule_name}: {', '.join(step.premises)} -> {step.conclusion} "
            f"(strength {step.conclusion_strength:.2f})"
        )

    return summary


def _matching_trace_steps(
    reasoning_result: ForwardChainingResult,
    target_fact: str,
) -> list[Any]:
    """Return forward-trace steps most relevant to the target fact."""
    direct_steps = [step for step in reasoning_result.trace if step.conclusion == target_fact]
    if direct_steps:
        return direct_steps

    if target_fact == "high_risk":
        related = {"medium_risk"}
    elif target_fact == "medium_risk":
        related = {"moderate_stress", "moderate_confidence", "average_quiz_performance"}
    else:
        related = {"balanced_workload", "manageable_stress", "strong_quiz_performance"}

    return [step for step in reasoning_result.trace if step.conclusion in related]


def _label_from_score(score: int) -> str:
    """Convert a numeric score back into a risk label."""
    for label, label_score in RISK_SCORES.items():
        if label_score == score:
            return label
    return "Medium"
