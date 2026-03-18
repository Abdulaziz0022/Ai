"""Feature-building helpers for the machine learning layer.

The ML component uses a small numeric feature set that is easy to explain in a
coursework report. Raw values come either from ``historical_students.csv`` or
from the existing ``StudentProfile`` model. Two simple engineered features are
also added:

- ``workload_gap``: workload hours minus free hours
- ``hours_per_deadline``: workload hours divided by the number of deadlines
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from student_success_copilot.models.student_profile import StudentProfile


RAW_FEATURE_COLUMNS = [
    "deadlines_count",
    "workload_hours",
    "free_hours",
    "confidence",
    "stress",
    "attendance",
    "quiz_score",
    "time_spent",
]

ENGINEERED_FEATURE_COLUMNS = [
    "workload_gap",
    "hours_per_deadline",
]

FEATURE_COLUMNS = RAW_FEATURE_COLUMNS + ENGINEERED_FEATURE_COLUMNS
TARGET_COLUMN = "risk_level"


def load_historical_data(csv_path: str | Path) -> pd.DataFrame:
    """Load the historical student dataset from CSV."""
    return pd.read_csv(csv_path)


def profile_to_feature_dict(profile: StudentProfile) -> dict[str, float | None]:
    """Convert one ``StudentProfile`` into a feature dictionary."""
    raw_values: dict[str, float | None] = {
        "deadlines_count": float(len(profile.tasks)),
        "workload_hours": float(profile.total_workload_hours()),
        "free_hours": float(profile.total_available_hours()),
        "confidence": _optional_float(profile.confidence),
        "stress": _optional_float(profile.stress),
        "attendance": _optional_float(profile.attendance),
        "quiz_score": _optional_float(profile.quiz_score),
        "time_spent": _optional_float(profile.time_spent),
    }
    return add_engineered_features(raw_values)


def build_feature_frame_from_profiles(
    profiles: Iterable[StudentProfile],
) -> pd.DataFrame:
    """Build a feature DataFrame from one or more student profiles."""
    rows = [profile_to_feature_dict(profile) for profile in profiles]
    return pd.DataFrame(rows, columns=FEATURE_COLUMNS)


def build_single_profile_frame(profile: StudentProfile) -> pd.DataFrame:
    """Build a one-row DataFrame for a single student profile."""
    return build_feature_frame_from_profiles([profile])


def prepare_feature_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Validate the raw columns and return a model-ready feature DataFrame."""
    missing_columns = [column for column in RAW_FEATURE_COLUMNS if column not in dataframe.columns]
    if missing_columns:
        missing_text = ", ".join(missing_columns)
        raise ValueError(f"Missing required feature column(s): {missing_text}")

    feature_frame = dataframe[RAW_FEATURE_COLUMNS].copy()
    feature_frame = add_engineered_features_to_frame(feature_frame)
    return feature_frame[FEATURE_COLUMNS]


def build_training_data(dataframe: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Split a dataset into feature matrix ``X`` and target labels ``y``."""
    if TARGET_COLUMN not in dataframe.columns:
        raise ValueError(f"Missing target column: {TARGET_COLUMN}")

    X = prepare_feature_dataframe(dataframe)
    y = dataframe[TARGET_COLUMN].astype(str)
    return X, y


def add_engineered_features(row: dict[str, float | None]) -> dict[str, float | None]:
    """Add coursework-friendly engineered features to one feature row."""
    deadlines_count = _safe_number(row.get("deadlines_count"))
    workload_hours = _safe_number(row.get("workload_hours"))
    free_hours = _safe_number(row.get("free_hours"))

    updated_row = dict(row)
    updated_row["workload_gap"] = workload_hours - free_hours
    updated_row["hours_per_deadline"] = (
        workload_hours / deadlines_count if deadlines_count > 0 else workload_hours
    )
    return updated_row


def add_engineered_features_to_frame(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Add the engineered features to a full DataFrame."""
    frame = dataframe.copy()
    frame["workload_gap"] = frame["workload_hours"] - frame["free_hours"]
    frame["hours_per_deadline"] = frame["workload_hours"] / frame["deadlines_count"].replace(0, 1)
    return frame


def _optional_float(value: object) -> float | None:
    """Convert a numeric value to float while keeping missing values as ``None``."""
    if value is None:
        return None
    return float(value)


def _safe_number(value: float | None) -> float:
    """Return a float value, treating missing values as 0.0."""
    if value is None or pd.isna(value):
        return 0.0
    return float(value)
