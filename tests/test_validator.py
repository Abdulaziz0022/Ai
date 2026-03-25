from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from student_success_copilot.models.student_profile import StudentProfile
from student_success_copilot.models.task import Task
from student_success_copilot.validator import validate_profile


def make_profile() -> StudentProfile:
    return StudentProfile(
        name="Test Student",
        tasks=[Task(title="Essay", deadline="Friday", estimated_hours=4, priority=3)],
        availability={"Monday": 2.0, "Wednesday": 2.0},
        confidence=6,
        stress=5,
        attendance=85,
        quiz_score=70,
        time_spent=4,
    )


def test_validator_detects_missing_tasks() -> None:
    profile = make_profile()
    profile.tasks = []

    result = validate_profile(profile)

    assert "tasks" in result.missing_fields


def test_validator_detects_missing_availability() -> None:
    profile = make_profile()
    profile.availability = {}

    result = validate_profile(profile)

    assert "availability" in result.missing_fields


def test_validator_detects_missing_confidence_and_stress() -> None:
    profile = make_profile()
    profile.confidence = None
    profile.stress = None

    result = validate_profile(profile)

    assert "confidence" in result.missing_fields
    assert "stress" in result.missing_fields


def test_validator_detects_confidence_quiz_contradiction() -> None:
    profile = make_profile()
    profile.confidence = 9
    profile.quiz_score = 42

    result = validate_profile(profile)

    assert any("quiz score" in item.lower() for item in result.contradictions)
