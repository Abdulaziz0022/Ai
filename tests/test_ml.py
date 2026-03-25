from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
CSV_PATH = PROJECT_ROOT / "data" / "historical_students.csv"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from student_success_copilot.ml.evaluate import evaluate_model
from student_success_copilot.ml.features import load_historical_data
from student_success_copilot.ml.predict import predict_risk
from student_success_copilot.ml.train import train_risk_model
from student_success_copilot.models.student_profile import StudentProfile
from student_success_copilot.models.task import Task


def make_ml_profile() -> StudentProfile:
    return StudentProfile(
        name="ML Case",
        tasks=[
            Task(title="Project draft", deadline="Thursday", estimated_hours=5, priority=3),
            Task(title="Revision", deadline="Friday", estimated_hours=3, priority=2),
        ],
        availability={"Monday": 2.0, "Tuesday": 2.0, "Wednesday": 1.0},
        confidence=5,
        stress=7,
        attendance=76,
        quiz_score=61,
        time_spent=3,
    )


def test_historical_students_csv_loads_correctly() -> None:
    dataframe = load_historical_data(CSV_PATH)

    assert len(dataframe) >= 30
    assert "risk_level" in dataframe.columns
    assert "workload_hours" in dataframe.columns


def test_model_training_runs_without_crashing() -> None:
    trained_model = train_risk_model(csv_path=CSV_PATH)

    assert trained_model.model is not None
    assert len(trained_model.X_train) > 0
    assert len(trained_model.X_test) > 0


def test_prediction_returns_valid_risk_label() -> None:
    trained_model = train_risk_model(csv_path=CSV_PATH)
    prediction = predict_risk(trained_model, make_ml_profile())

    assert prediction.predicted_risk in {"Low", "Medium", "High"}


def test_evaluation_returns_required_metrics() -> None:
    trained_model = train_risk_model(csv_path=CSV_PATH)
    evaluation = evaluate_model(trained_model)

    assert 0.0 <= evaluation.accuracy <= 1.0
    assert 0.0 <= evaluation.precision <= 1.0
    assert 0.0 <= evaluation.recall <= 1.0
    assert 0.0 <= evaluation.f1_score <= 1.0
    assert not evaluation.confusion_matrix_table.empty
