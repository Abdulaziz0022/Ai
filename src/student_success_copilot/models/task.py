"""Task model for assignments, exams, and study activities."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Task:
    """Represent a study task with a deadline and estimated workload."""

    title: str
    deadline: str
    estimated_hours: float
    priority: int = 2

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create a Task from a dictionary."""
        return cls(
            title=str(data.get("title", "Untitled task")),
            deadline=str(data.get("deadline", "Unknown")),
            estimated_hours=float(data.get("estimated_hours", 1.0)),
            priority=int(data.get("priority", 2)),
        )

    def to_dict(self) -> dict:
        """Convert the task into a dictionary."""
        return {
            "title": self.title,
            "deadline": self.deadline,
            "estimated_hours": self.estimated_hours,
            "priority": self.priority,
        }
