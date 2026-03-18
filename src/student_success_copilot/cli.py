"""Command-line interface helpers for Student Success Copilot."""

from __future__ import annotations

from student_success_copilot.input_handler import (
    collect_student_input,
    load_student_input_from_json,
)
from student_success_copilot.pipeline import PipelineResult, run_copilot


def run_cli() -> None:
    """Run the simple terminal interface."""
    print("=" * 60)
    print("Student Success Copilot")
    print("=" * 60)
    print("This starter version can use sample data or manual input.")
    print()

    choice = input("Choose an option: [1] Sample input, [2] Manual input: ").strip()

    if choice == "2":
        profile = collect_student_input()
    else:
        profile = load_student_input_from_json()

    result = run_copilot(profile)
    display_results(result)


def display_results(result: PipelineResult) -> None:
    """Print the main outputs in a clear beginner-friendly format."""
    print()
    print("-" * 60)
    print("Final Result")
    print("-" * 60)
    print(f"Student: {result.profile.name}")
    print(f"Risk level: {result.risk_level}")
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

    if result.question_history:
        print()
        print("Question Loop:")
        for entry in result.question_history:
            print(f"- {entry}")

    print()
    print("Explanation:")
    print(result.explanation)