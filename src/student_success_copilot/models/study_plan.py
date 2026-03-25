"""Study plan models used by the starter pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StudySession:
    """One scheduled study session in the weekly plan."""

    day: str
    task_title: str
    hours: float
    deadline: str = ""
    priority: int | None = None
    days_left_display: int | None = None

    def to_display_line(self) -> str:
        """Return one user-friendly display line for the terminal."""
        line = f"{self.day}: {self.task_title} for {self.hours:.1f} hour(s)"

        details: list[str] = []
        if self.deadline:
            details.append(f"Deadline: {self.deadline}")
        if self.priority is not None:
            details.append(f"priority {self.priority}")
        if self.days_left_display is not None:
            details.append(f"days left {self.days_left_display}")

        if details:
            line += f" [{' ; '.join(details).replace(' ;', ';')}]"

        return line


@dataclass
class WeeklyStudyPlan:
    """A simple container for all scheduled sessions in one week."""

    sessions: list[StudySession] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def add_session(self, session: StudySession) -> None:
        """Add a new session to the weekly plan."""
        self.sessions.append(session)

    def total_planned_hours(self) -> float:
        """Return the total number of planned study hours."""
        return sum(session.hours for session in self.sessions)

    def to_display_lines(self) -> list[str]:
        """Return user-friendly lines for terminal display."""
        return [session.to_display_line() for session in self.sessions]
