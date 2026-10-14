"""Train and compare SafeWeb models on the audited PhishVN 5,000-row dataset.

This script intentionally uses a domain-disjoint fallback split because the
PhishVN release does not ship a separate validation or test file in this repo.
The split is reproducible and preserves the training split for model fitting only.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

import joblib
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_quality import domain_disjoint_split
from src.feature_extractor import extract_features
from src.predict import DEFAULT_MODEL_PATH
DATASET_PATH = PROJECT_ROOT / "data" / "raw" / "PhishVN_training_5000.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "phishvn_domain_eval.json"
LEGACY_MODEL_PATH = PROJECT_ROOT / "model" / "random_forest_legacy.joblib"


def build_feature_frame(urls: pd.Series) -> pd.DataFrame:
    return pd.DataFrame([extract_features(url) for url in urls])


def evaluate_model(model, X_test: pd.DataFrame, y_test: pd.Series) -> dict[str, float | list[int] | dict[str, float]]:
    predictions = model.predict(X_test)
    matrix = confusion_matrix(y_test, predictions, labels=[0, 1])
    return {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "precision": float(precision_score(y_test, predictions, zero_division=0)),
        "recall": float(recall_score(y_test, predictions, zero_division=0)),
        "f1_score": float(f1_score(y_test, predictions, zero_division=0)),
        "confusion_matrix": matrix.tolist(),
        "class_report": {
            "benign": {
                "precision": float(precision_score(y_test, predictions, labels=[0], average=None, zero_division=0)[0]),
                "recall": float(recall_score(y_test, predictions, labels=[0], average=None, zero_division=0)[0]),
                "f1_score": float(f1_score(y_test, predictions, labels=[0], average=None, zero_division=0)[0]),
                "support": int((y_test == 0).sum()),
            },
            "phishing": {
                "precision": float(precision_score(y_test, predictions, labels=[1], average=None, zero_division=0)[0]),
                "recall": float(recall_score(y_test, predictions, labels=[1], average=None, zero_division=0)[0]),
                "f1_score": float(f1_score(y_test, predictions, labels=[1], average=None, zero_division=0)[0]),
                "support": int((y_test == 1).sum()),
            },
        },
    }


def save_model(model, feature_names: list[str], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "feature_names": feature_names}, destination)


def main() -> None:
    dataset = pd.read_csv(DATASET_PATH)
    train_frame, test_frame = domain_disjoint_split(DATASET_PATH, test_size=0.20, random_state=42)
    X_train = build_feature_frame(train_frame["url"])
    X_test = build_feature_frame(test_frame["url"])
    y_train = train_frame["label"]
    y_test = test_frame["label"]

    candidates = {
        "random_forest": RandomForestClassifier(n_estimators=200, random_state=42),
        "gradient_boosting": GradientBoostingClassifier(random_state=42),
    }

    evaluated = {}
    for name, model in candidates.items():
        model.fit(X_train, y_train)
        evaluated[name] = evaluate_model(model, X_test, y_test)

    selected_name = "random_forest"
    selected_model = candidates[selected_name]
    feature_names = list(X_train.columns)
    if DEFAULT_MODEL_PATH.exists() and not LEGACY_MODEL_PATH.exists():
        shutil.copy2(DEFAULT_MODEL_PATH, LEGACY_MODEL_PATH)
    save_model(selected_model, feature_names, DEFAULT_MODEL_PATH)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "dataset": str(DATASET_PATH),
        "split": "domain_disjoint_fallback",
        "train_rows": int(len(train_frame)),
        "test_rows": int(len(test_frame)),
        "train_labels": {"benign": int((y_train == 0).sum()), "phishing": int((y_train == 1).sum())},
        "test_labels": {"benign": int((y_test == 0).sum()), "phishing": int((y_test == 1).sum())},
        "evaluations": evaluated,
        "selected_model": selected_name,
    }
    REPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"selected_model": selected_name, **evaluated[selected_name]}, indent=2))


if __name__ == "__main__":
    main()
