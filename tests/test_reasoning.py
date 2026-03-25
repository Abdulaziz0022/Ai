from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from student_success_copilot.models.student_profile import StudentProfile
from student_success_copilot.models.task import Task
from student_success_copilot.reasoning.backward_chain import backward_chain
from student_success_copilot.reasoning.facts import build_initial_facts
from student_success_copilot.reasoning.forward_chain import forward_chain


def make_risky_profile() -> StudentProfile:
    return StudentProfile(
        name="Risky Case",
        tasks=[
            Task(title="Math report", deadline="Monday", estimated_hours=5, priority=3),
            Task(title="Programming lab", deadline="Tuesday", estimated_hours=4, priority=3),
            Task(title="Revision", deadline="Wednesday", estimated_hours=3, priority=2),
            Task(title="Essay", deadline="Thursday", estimated_hours=3, priority=2),
        ],
        availability={"Monday": 1.0, "Tuesday": 1.0, "Wednesday": 1.0},
        confidence=4,
        stress=8,
        attendance=65,
        quiz_score=45,
        time_spent=2,
    )


def test_build_initial_facts_creates_expected_facts() -> None:
    facts = build_initial_facts(make_risky_profile())

    assert "overloaded_schedule" in facts
    assert "high_stress" in facts
    assert "low_confidence" in facts


def test_forward_chain_inferrs_risk_in_risky_case() -> None:
    facts = build_initial_facts(make_risky_profile())
    result = forward_chain(facts)

    assert "high_risk" in result.facts or "medium_risk" in result.facts


def test_backward_chain_proves_high_risk_in_risky_case() -> None:
    facts = build_initial_facts(make_risky_profile())
    forward_result = forward_chain(facts)
    proof = backward_chain("high_risk", forward_result.facts)

    assert proof.proved is True
    assert proof.strength > 0
    assert proof.proof_path
