"""Student profile model used across the starter project."""

from __future__ import annotations

from dataclasses import dataclass, field

from student_success_copilot.models.task import Task


@dataclass
class StudentProfile:
    """Store the main information collected about a student."""

    name: str
    tasks: list[Task] = field(default_factory=list)
    availability: dict[str, float] = field(default_factory=dict)
    confidence: int | None = None
    stress: int | None = None
    attendance: float | None = None
    quiz_score: float | None = None
    time_spent: float | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "StudentProfile":
        """Build a StudentProfile from a plain dictionary."""
        task_items = [Task.from_dict(item) for item in data.get("tasks", [])]
        availability = {
            str(day): float(hours)
            for day, hours in data.get("availability", {}).items()
        }

        return cls(
            name=str(data.get("name", "Student")),
            tasks=task_items,
            availability=availability,
            confidence=_to_optional_int(data.get("confidence")),
            stress=_to_optional_int(data.get("stress")),
            attendance=_to_optional_float(data.get("attendance")),
            quiz_score=_to_optional_float(data.get("quiz_score")),
            time_spent=_to_optional_float(data.get("time_spent")),
        )

    def to_dict(self) -> dict:
        """Convert the profile into a dictionary for saving or debugging."""
        return {
            "name": self.name,
            "tasks": [task.to_dict() for task in self.tasks],
            "availability": self.availability,
            "confidence": self.confidence,
            "stress": self.stress,
            "attendance": self.attendance,
            "quiz_score": self.quiz_score,
            "time_spent": self.time_spent,
        }

    def total_workload_hours(self) -> float:
        """Return the sum of all task workload estimates."""
        return sum(task.estimated_hours for task in self.tasks)

    def total_available_hours(self) -> float:
        """Return the total study availability for the week."""
        return sum(self.availability.values())


def _to_optional_int(value: object) -> int | None:
    """Convert a value to an int if possible, otherwise return None."""
    if value in (None, ""):
        return None
    return int(value)


def _to_optional_float(value: object) -> float | None:
    """Convert a value to a float if possible, otherwise return None."""
    if value in (None, ""):
        return None
    return float(value)
