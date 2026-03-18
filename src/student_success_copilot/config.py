"""Project-wide configuration values for the starter application."""

from __future__ import annotations

from pathlib import Path


APP_NAME = "Student Success Copilot"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
SAMPLE_INPUT_PATH = DATA_DIR / "sample_student_input.json"

DEFAULT_STUDY_DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

REQUIRED_PROFILE_FIELDS = [
    "tasks",
    "availability",
    "confidence",
    "stress",
]

LOW_CONFIDENCE_THRESHOLD = 4
HIGH_STRESS_THRESHOLD = 8
DEFAULT_SESSION_LENGTH_HOURS = 2.0
