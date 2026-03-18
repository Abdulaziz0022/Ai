"""Study plan models used by the starter pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StudySession:
    """One scheduled study session in the weekly plan."""

    day: str
    task_title: str
    hours: float
    notes: str = ""


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
        lines: list[str] = []
        for session in self.sessions:
            line = f"{session.day}: {session.task_title} for {session.hours:.1f} hour(s)"
            if session.notes:
                line += f" [{session.notes}]"
            lines.append(line)
        return lines
