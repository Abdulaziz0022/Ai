"""Interactive follow-up questions for missing or conflicting input."""

from __future__ import annotations

from student_success_copilot.models.student_profile import StudentProfile
from student_success_copilot.models.task import Task
from student_success_copilot.validator import ValidationResult


def run_question_loop(
    profile: StudentProfile,
    validation_result: ValidationResult,
) -> tuple[StudentProfile, list[str]]:
    """Ask follow-up questions to fill gaps or clarify contradictions."""
    history: list[str] = []

    if validation_result.missing_fields or validation_result.contradictions:
        print()
        print("A quick follow-up is needed before creating your study plan.")

    for field_name in validation_result.missing_fields:
        if field_name == "confidence":
            value = _ask_int_in_range("What is your current confidence level (1-10)? ")
            profile.confidence = value
            history.append(f"Filled missing confidence with value {value}.")

        elif field_name == "stress":
            value = _ask_int_in_range("What is your current stress level (1-10)? ")
            profile.stress = value
            history.append(f"Filled missing stress with value {value}.")

        elif field_name == "availability":
            total_hours = _ask_float("How many hours are you free to study this week? ")
            profile.availability = {
                "Monday": round(total_hours / 2, 1),
                "Wednesday": round(total_hours / 4, 1),
                "Friday": round(total_hours / 4, 1),
            }
            history.append(
                "Filled missing availability by spreading reported hours across the week."
            )

        elif field_name == "tasks":
            print("Please enter one study task so the system can create a plan.")
            title = input("Task title: ").strip() or "General study task"
            deadline = input("Deadline: ").strip() or "Unknown"
            hours = _ask_float("Estimated hours needed: ")
            profile.tasks.append(
                Task(title=title, deadline=deadline, estimated_hours=hours)
            )
            history.append(f"Added a task called '{title}'.")

    for contradiction in validation_result.contradictions:
        if "quiz score" in contradiction.lower():
            value = _ask_int_in_range(
                "Your confidence and quiz score do not match well. "
                "Please confirm your confidence now (1-10): "
            )
            profile.confidence = value
            history.append(
                f"Updated confidence to {value} after checking the quiz-score conflict."
            )

        elif "workload" in contradiction.lower():
            extra_hours = _ask_float(
                "Your workload is larger than your free time. "
                "How many extra study hours can you add this week? "
            )
            profile.availability["Saturday"] = profile.availability.get("Saturday", 0.0) + extra_hours
            history.append(
                f"Added {extra_hours:.1f} extra study hour(s) to Saturday."
            )

    return profile, history


def _ask_int_in_range(prompt_text: str, minimum: int = 1, maximum: int = 10) -> int:
    """Prompt until the user enters an integer inside the given range."""
    while True:
        raw_value = input(prompt_text).strip()
        try:
            value = int(raw_value)
        except ValueError:
            print("Please enter a whole number.")
            continue

        if minimum <= value <= maximum:
            return value

        print(f"Please enter a number between {minimum} and {maximum}.")


def _ask_float(prompt_text: str) -> float:
    """Prompt until the user enters a valid float."""
    while True:
        raw_value = input(prompt_text).strip()
        try:
            value = float(raw_value)
        except ValueError:
            print("Please enter a valid number.")
            continue

        if value >= 0:
            return value

        print("Please enter a non-negative number.")
