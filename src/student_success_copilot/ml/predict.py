"""Prediction helpers for one student profile."""

from __future__ import annotations

from dataclasses import dataclass, field

from student_success_copilot.ml.features import build_single_profile_frame
from student_success_copilot.ml.train import TrainedRiskModel
from student_success_copilot.models.student_profile import StudentProfile


@dataclass
class PredictionResult:
    """Store the predicted risk label and optional probabilities."""

    predicted_risk: str
    probabilities: dict[str, float] = field(default_factory=dict)


def predict_risk(
    trained_model: TrainedRiskModel,
    profile: StudentProfile,
) -> PredictionResult:
    """Predict the risk level for one student profile."""
    feature_frame = build_single_profile_frame(profile)
    ordered_features = feature_frame[trained_model.feature_columns]

    predicted_label = str(trained_model.model.predict(ordered_features)[0])
    probabilities = _predict_probabilities(trained_model, ordered_features)

    return PredictionResult(
        predicted_risk=predicted_label,
        probabilities=probabilities,
    )


def _predict_probabilities(
    trained_model: TrainedRiskModel,
    ordered_features,
) -> dict[str, float]:
    """Return class probabilities when the fitted model supports them."""
    if not hasattr(trained_model.model, "predict_proba"):
        return {}

    probability_values = trained_model.model.predict_proba(ordered_features)[0]
    return {
        label: round(float(probability), 4)
        for label, probability in zip(trained_model.label_values, probability_values)
    }
