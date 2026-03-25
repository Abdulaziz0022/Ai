"""Training helpers for the Student Success Copilot ML layer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from student_success_copilot import config
from student_success_copilot.ml.features import (
    FEATURE_COLUMNS,
    build_training_data,
    load_historical_data,
)


DEFAULT_DATASET_PATH = config.DATA_DIR / "historical_students.csv"


@dataclass
class TrainedRiskModel:
    """Store the fitted classifier and the data split used for evaluation."""

    model: Pipeline
    feature_columns: list[str]
    label_values: list[str]
    X_train: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_test: pd.Series


def build_classifier() -> Pipeline:
    """Create a simple logistic regression pipeline.

    The older local sklearn build does not accept the newer ``multi_class``
    argument used in some generated versions of this file, so the model stays
    with broadly compatible defaults here.
    """
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(max_iter=1000)),
        ]
    )


def train_risk_model(
    csv_path: str | Path = DEFAULT_DATASET_PATH,
    test_size: float = 0.25,
    random_state: int = 42,
) -> TrainedRiskModel:
    """Load the dataset, split it, and train the classifier."""
    dataset_path = Path(csv_path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    dataset = load_historical_data(dataset_path)
    return train_risk_model_from_dataframe(
        dataset,
        test_size=test_size,
        random_state=random_state,
    )


def train_risk_model_from_dataframe(
    dataframe: pd.DataFrame,
    test_size: float = 0.25,
    random_state: int = 42,
) -> TrainedRiskModel:
    """Train the classifier from an already loaded DataFrame."""
    X, y = build_training_data(dataframe)

    if len(dataframe) < 6:
        raise ValueError("The dataset is too small to train and evaluate the model safely.")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    model = build_classifier()
    model.fit(X_train, y_train)

    classifier = model.named_steps["classifier"]
    label_values = [str(label) for label in classifier.classes_]

    return TrainedRiskModel(
        model=model,
        feature_columns=list(FEATURE_COLUMNS),
        label_values=label_values,
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test,
    )
