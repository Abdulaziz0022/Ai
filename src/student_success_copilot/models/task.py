"""Task model for assignments, exams, and study activities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class Task:
    """Represent a study task with a deadline and estimated workload."""

    title: str
    deadline: str
    estimated_hours: float
    priority: int = 2
    days_left: int | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create a task from a dictionary."""
        deadline = str(data.get("deadline", "Unknown"))
        raw_days_left = data.get("days_left")
        days_left = _to_optional_days_left(raw_days_left)

        if days_left is None:
            days_left = _infer_days_left_from_deadline(deadline)

        return cls(
            title=str(data.get("title", "Untitled task")),
            deadline=deadline,
            estimated_hours=float(data.get("estimated_hours", 1.0)),
            priority=int(data.get("priority", 2)),
            days_left=days_left,
        )

    def to_dict(self) -> dict:
        """Convert the task into a dictionary."""
        return {
            "title": self.title,
            "deadline": self.deadline,
            "estimated_hours": self.estimated_hours,
            "priority": self.priority,
            "days_left": self.days_left,
        }


def _to_optional_days_left(value: object) -> int | None:
    """Convert a value to a non-negative integer when possible."""
    if value in (None, ""):
        return None

    converted = int(value)
    return max(0, converted)


def _infer_days_left_from_deadline(deadline: str) -> int | None:
    """Infer days left from either an ISO date or a weekday name."""
    cleaned_deadline = deadline.strip()
    today = date.today()

    weekday_offsets = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    if cleaned_deadline.lower() in weekday_offsets:
        target_weekday = weekday_offsets[cleaned_deadline.lower()]
        current_weekday = today.weekday()
        delta = (target_weekday - current_weekday) % 7
        return delta

    try:
        deadline_date = datetime.strptime(cleaned_deadline, "%Y-%m-%d").date()
    except ValueError:
        return None

    return max(0, (deadline_date - today).days)
