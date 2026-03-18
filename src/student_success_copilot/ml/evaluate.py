"""Evaluation helpers for the coursework machine learning component."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)

from student_success_copilot.ml.train import TrainedRiskModel


@dataclass
class EvaluationResult:
    """Store coursework-friendly evaluation metrics."""

    accuracy: float
    precision: float
    recall: float
    f1_score: float
    confusion_matrix_table: pd.DataFrame
    classification_report_text: str

    def to_dict(self) -> dict[str, object]:
        """Convert the metrics into a simple dictionary."""
        return {
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "confusion_matrix": self.confusion_matrix_table.to_dict(),
            "classification_report": self.classification_report_text,
        }


def evaluate_model(trained_model: TrainedRiskModel) -> EvaluationResult:
    """Evaluate the fitted classifier on its stored test split."""
    y_true = trained_model.y_test
    y_pred = trained_model.model.predict(trained_model.X_test[trained_model.feature_columns])
    labels = trained_model.label_values

    accuracy = float(accuracy_score(y_true, y_pred))
    precision, recall, f1_score, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        average="weighted",
        zero_division=0,
    )

    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    matrix_table = pd.DataFrame(
        matrix,
        index=[f"Actual {label}" for label in labels],
        columns=[f"Predicted {label}" for label in labels],
    )

    report_text = classification_report(
        y_true,
        y_pred,
        labels=labels,
        zero_division=0,
    )

    return EvaluationResult(
        accuracy=round(accuracy, 4),
        precision=round(float(precision), 4),
        recall=round(float(recall), 4),
        f1_score=round(float(f1_score), 4),
        confusion_matrix_table=matrix_table,
        classification_report_text=report_text,
    )
