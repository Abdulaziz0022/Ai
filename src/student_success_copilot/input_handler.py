"""Input collection helpers for sample and manual student data."""

from __future__ import annotations

import json
from pathlib import Path

from student_success_copilot import config
from student_success_copilot.models.student_profile import StudentProfile
from student_success_copilot.models.task import Task


def collect_student_input() -> StudentProfile:
    """Collect a simple student profile from terminal prompts."""
    print()
    print("Manual Input")
    print("Press Enter to skip any optional field.")

    name = input("Student name: ").strip() or "Student"

    tasks = _collect_tasks()
    availability = _collect_availability()
    confidence = _prompt_optional_int("Confidence level (1-10): ")
    stress = _prompt_optional_int("Stress level (1-10): ")
    attendance = _prompt_optional_float("Attendance percentage (optional): ")
    quiz_score = _prompt_optional_float("Average quiz score (optional): ")
    time_spent = _prompt_optional_float("Hours already studied this week (optional): ")

    return StudentProfile(
        name=name,
        tasks=tasks,
        availability=availability,
        confidence=confidence,
        stress=stress,
        attendance=attendance,
        quiz_score=quiz_score,
        time_spent=time_spent,
    )


def load_student_input_from_json(file_path: str | Path | None = None) -> StudentProfile:
    """Load sample input from JSON, or fall back to built-in sample data."""
    path = Path(file_path) if file_path else config.SAMPLE_INPUT_PATH

    if path.exists():
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    else:
        data = get_default_sample_data()

    return StudentProfile.from_dict(data)


def get_default_sample_data() -> dict:
    """Return built-in sample data so the app runs even without a JSON file."""
    return {
        "name": "Alex",
        "tasks": [
            {
                "title": "Math assignment",
                "deadline": "Friday",
                "estimated_hours": 4,
                "priority": 3,
            },
            {
                "title": "Programming quiz revision",
                "deadline": "Thursday",
                "estimated_hours": 3,
                "priority": 2,
            },
        ],
        "availability": {
            "Monday": 2,
            "Tuesday": 2,
            "Wednesday": 1.5,
            "Thursday": 2,
            "Friday": 1,
        },
        "confidence": 6,
        "stress": 7,
        "attendance": 82,
        "quiz_score": 64,
        "time_spent": 5,
    }


def _collect_tasks() -> list[Task]:
    """Ask the user to enter one or more tasks."""
    tasks: list[Task] = []
    raw_count = input("How many tasks or deadlines do you want to enter? ").strip()
    task_count = int(raw_count) if raw_count.isdigit() else 0

    for index in range(task_count):
        print()
        print(f"Task {index + 1}")
        title = input("Title: ").strip() or f"Task {index + 1}"
        deadline = input("Deadline (for example Friday or 2026-03-25): ").strip() or "Unknown"
        estimated_hours = _prompt_optional_float("Estimated hours: ") or 1.0
        priority = _prompt_optional_int("Priority (1-3, optional): ") or 2
        tasks.append(
            Task(
                title=title,
                deadline=deadline,
                estimated_hours=estimated_hours,
                priority=priority,
            )
        )

    return tasks


def _collect_availability() -> dict[str, float]:
    """Ask the user for study availability for each day of the week."""
    availability: dict[str, float] = {}
    print()
    print("Enter available study hours for each day.")

    for day in config.DEFAULT_STUDY_DAYS:
        hours = _prompt_optional_float(f"{day}: ")
        if hours is not None and hours > 0:
            availability[day] = hours

    return availability


def _prompt_optional_int(prompt_text: str) -> int | None:
    """Prompt for an optional integer."""
    raw_value = input(prompt_text).strip()
    if raw_value == "":
        return None
    try:
        return int(raw_value)
    except ValueError:
        print("Invalid number. Leaving this field blank.")
        return None


def _prompt_optional_float(prompt_text: str) -> float | None:
    """Prompt for an optional float."""
    raw_value = input(prompt_text).strip()
    if raw_value == "":
        return None
    try:
        return float(raw_value)
    except ValueError:
        print("Invalid number. Leaving this field blank.")
        return None
