"""Command-line interface helpers for Student Success Copilot."""

from __future__ import annotations

from student_success_copilot.input_handler import (
    collect_student_input,
    load_student_input_from_json,
)
from student_success_copilot.pipeline import PipelineResult, run_copilot


def run_cli() -> None:
    """Run the terminal interface."""
    print("=" * 60)
    print("Student Success Copilot")
    print("=" * 60)
    print("Choose sample data or enter your own details.")
    print()

    choice = input("Choose an option: [1] Sample input, [2] Manual input: ").strip()

    if choice == "2":
        profile = collect_student_input()
    else:
        profile = load_student_input_from_json()

    result = run_copilot(profile)
    display_results(result)


def display_results(result: PipelineResult) -> None:
    """Print the integrated AI outputs in a clean format."""
    print()
    print("-" * 60)
    print("Final Result")
    print("-" * 60)
    print(f"Student: {result.profile.name}")
    print(f"Final risk level: {result.risk_level}")
    print(f"Rule-based risk: {result.rule_risk_level}")
    print(f"ML risk: {result.ml_risk_level or 'Unavailable'}")

    if result.disagreement_note:
        print(f"Risk merge note: {result.disagreement_note}")

    print()
    print("Recommendations:")
    for item in result.recommendations:
        print(f"- {item}")

    print()
    print("Weekly Study Plan:")
    if result.study_plan.sessions:
        for line in result.study_plan.to_display_lines():
            print(f"- {line}")
    else:
        print("- No study sessions were created.")

    if result.study_plan.notes:
        print()
        print("Plan Notes:")
        for note in result.study_plan.notes:
            print(f"- {note}")

    if result.planning_summary:
        print()
        print("Planning Comparison:")
        for line in result.planning_summary:
            print(f"- {line}")

    if result.risk_reasons:
        print()
        print("Risk Reasons:")
        for reason in result.risk_reasons:
            print(f"- {reason}")

    if result.reasoning_trace:
        print()
        print("Reasoning Trace:")
        for line in result.reasoning_trace:
            print(f"- {line}")

    if result.proof_summary:
        print()
        print("Backward-Chaining Proof:")
        for line in result.proof_summary:
            print(f"- {line}")

    if result.ml_summary:
        print()
        print("Machine Learning:")
        for line in result.ml_summary:
            print(f"- {line}")

    if result.question_history:
        print()
        print("Question Loop Impact:")
        for entry in result.question_history:
            print(f"- {entry}")

    print()
    print("Explanation:")
    print(result.explanation)
