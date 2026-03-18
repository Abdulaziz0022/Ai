"""Validation helpers for missing fields and simple contradictions."""

from __future__ import annotations

from dataclasses import dataclass, field

from student_success_copilot.models.student_profile import StudentProfile


@dataclass
class ValidationResult:
    """Store validation findings for a student profile."""

    missing_fields: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        """Return True when follow-up questions may be useful."""
        return bool(self.missing_fields or self.contradictions)


def validate_profile(profile: StudentProfile) -> ValidationResult:
    """Check whether a profile has missing information or simple conflicts."""
    result = ValidationResult()

    if not profile.tasks:
        result.missing_fields.append("tasks")

    if not profile.availability or profile.total_available_hours() <= 0:
        result.missing_fields.append("availability")

    if profile.confidence is None:
        result.missing_fields.append("confidence")

    if profile.stress is None:
        result.missing_fields.append("stress")

    if profile.confidence is not None and not 1 <= profile.confidence <= 10:
        result.warnings.append("Confidence should normally be between 1 and 10.")

    if profile.stress is not None and not 1 <= profile.stress <= 10:
        result.warnings.append("Stress should normally be between 1 and 10.")

    if (
        profile.confidence is not None
        and profile.quiz_score is not None
        and profile.confidence >= 8
        and profile.quiz_score < 50
    ):
        result.contradictions.append(
            "Confidence is very high, but the quiz score is quite low."
        )

    if (
        profile.total_workload_hours() > 0
        and profile.total_available_hours() > 0
        and profile.total_workload_hours() > profile.total_available_hours() + 5
    ):
        result.contradictions.append(
            "The workload is much higher than the available study time."
        )

    if profile.attendance is not None and profile.attendance < 60:
        result.warnings.append(
            "Attendance is low, which may increase study risk."
        )

    return result
