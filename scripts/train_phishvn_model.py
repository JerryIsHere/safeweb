"""Train SafeWeb on PhishVN's official grouped partitions and evaluate its test set."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_extractor import PHISHVN_FEATURE_NAMES, extract_features
from src.predict import DEFAULT_MODEL_PATH
DATASET_PATH = PROJECT_ROOT / "data" / "processed" / "phishvn_clean.csv"
DATABASE_PATH = PROJECT_ROOT / "data" / "phishvn_database.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "phishvn_domain_eval.json"
METRICS_PATH = PROJECT_ROOT / "reports" / "metrics.json"
SOURCE_FEATURE_NAMES = tuple(name.removeprefix("phishvn_") for name in PHISHVN_FEATURE_NAMES)


def build_feature_frame(frame: pd.DataFrame, database: dict[str, object]) -> pd.DataFrame:
    profiles = database.get("hostProfiles", {})
    suspicious_tlds = set(database.get("suspiciousTlds", []))
    values = []
    for url in frame["url"]:
        host = (urlsplit(url).hostname or "").lower()
        profile_values = profiles.get(host)
        profile_fields = database.get("hostProfileFields", [])
        profile = dict(zip(profile_fields, profile_values, strict=True)) if profile_values else None
        values.append(
            extract_features(
                url,
                domain_profile=profile,
                suspicious_tlds=suspicious_tlds,
            )
        )
    features = pd.DataFrame(values, index=frame.index)
    for source_name, model_name in zip(SOURCE_FEATURE_NAMES, PHISHVN_FEATURE_NAMES, strict=True):
        if source_name == "suspicious_tld":
            features[model_name] = frame[source_name].astype(float)
        else:
            features[model_name] = frame[model_name].astype(float)
    return features


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
    dataset = pd.read_csv(DATASET_PATH, low_memory=False)
    database = json.loads(DATABASE_PATH.read_text(encoding="utf-8"))
    train_frame = dataset[dataset["split"].isin(["train", "val"])].copy()
    test_frame = dataset[dataset["split"] == "test"].copy()
    if train_frame.empty or test_frame.empty:
        raise ValueError("The cleaned dataset must include train/val and test partitions.")
    X_train = build_feature_frame(train_frame, database)
    X_test = build_feature_frame(test_frame, database)
    y_train = train_frame["label"].astype(int)
    y_test = test_frame["label"].astype(int)

    selected_model = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced_subsample",
        max_depth=16,
        min_samples_leaf=3,
    )
    selected_model.fit(X_train, y_train)
    evaluation = evaluate_model(selected_model, X_test, y_test)
    feature_names = list(X_train.columns)
    save_model(selected_model, feature_names, DEFAULT_MODEL_PATH)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "dataset": str(DATASET_PATH),
        "dataset_source": "PhishVN v3.1.0 open archive",
        "split": "official_grouped_temporal_train_plus_val_test_untouched",
        "train_rows": int(len(train_frame)),
        "test_rows": int(len(test_frame)),
        "feature_count": len(feature_names),
        "features": feature_names,
        "pre_extracted_comp_phish_features_used": len(SOURCE_FEATURE_NAMES) - 1,
        "phishvn_pre_extracted_feature_columns_including_tld_flag": len(PHISHVN_FEATURE_NAMES),
        "test_domains_disjoint_from_train_val": True,
        "train_labels": {"benign": int((y_train == 0).sum()), "phishing": int((y_train == 1).sum())},
        "test_labels": {"benign": int((y_test == 0).sum()), "phishing": int((y_test == 1).sum())},
        "evaluations": {"random_forest": evaluation},
        "selected_model": "random_forest",
    }
    REPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    METRICS_PATH.write_text(
        json.dumps(
            {
                "dataset_source": "PhishVN v3.1.0 open archive",
                "accuracy": evaluation["accuracy"],
                "precision": evaluation["precision"],
                "recall": evaluation["recall"],
                "f1_score": evaluation["f1_score"],
                "confusion_matrix_labels": ["benign", "phishing"],
                "confusion_matrix": evaluation["confusion_matrix"],
                "test_rows": int(len(test_frame)),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"selected_model": "random_forest", **evaluation}, indent=2))


if __name__ == "__main__":
    main()
