"""Experimental URL feature and model evaluation separate from production."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

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
from sklearn.model_selection import train_test_split

from src.data_loader import load_dataset
from src.data_quality import analyze_dataset, domain_disjoint_split, normalize_url_for_similarity
from src.feature_extractor import EXPERIMENTAL_FEATURE_ORDER, extract_features
from src.train import RANDOM_STATE, TEST_SIZE, feature_frame


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTAL_MODEL_PATH = PROJECT_ROOT / "model" / "random_forest_experimental.joblib"
REPORT_DIR = PROJECT_ROOT / "reports" / "experimental"


def _baseline_feature_frame(urls: pd.Series) -> pd.DataFrame:
    return pd.DataFrame([extract_features(url) for url in urls])


def _experimental_feature_frame(urls: pd.Series) -> pd.DataFrame:
    return pd.DataFrame([extract_features(url, include_experimental=True) for url in urls])


def _mode_features(mode: str) -> tuple[str, callable]:
    if mode == "baseline":
        return "baseline", _baseline_feature_frame
    if mode == "experimental":
        return "experimental", _experimental_feature_frame
    raise ValueError(f"Unsupported feature mode: {mode}")


def _dataset_metrics(y_true: pd.Series, y_pred: pd.Series) -> dict[str, object]:
    matrix = confusion_matrix(y_true, y_pred, labels=[0, 1])
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "phishing_recall": float(recall_score(y_true, y_pred, labels=[1], pos_label=1, zero_division=0)),
        "false_positive_rate": float(
            matrix[0, 1] / (matrix[0, 1] + matrix[0, 0]) if (matrix[0, 1] + matrix[0, 0]) else 0.0
        ),
        "false_negative_rate": float(
            matrix[1, 0] / (matrix[1, 0] + matrix[1, 1]) if (matrix[1, 0] + matrix[1, 1]) else 0.0
        ),
        "confusion_matrix": matrix.tolist(),
    }


def train_experimental_model(
    dataset_path: str | Path,
    model_path: str | Path = EXPERIMENTAL_MODEL_PATH,
    *,
    feature_mode: str = "experimental",
) -> dict[str, object]:
    """Train a separate experimental model without changing the production model."""
    dataset = load_dataset(dataset_path)
    _, feature_builder = _mode_features(feature_mode)
    train_rows, _ = domain_disjoint_split(dataset_path, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    train_features = feature_builder(train_rows["url"])
    train_labels = train_rows["label"]
    model = RandomForestClassifier(n_estimators=200, random_state=RANDOM_STATE)
    model.fit(train_features, train_labels)
    destination = Path(model_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "model": model,
        "feature_names": list(train_features.columns),
        "feature_mode": feature_mode,
        "dataset": str(Path(dataset_path)),
        "split": "domain-disjoint",
    }
    joblib.dump(bundle, destination)
    return {
        "training_rows": int(len(train_rows)),
        "feature_count": int(len(train_features.columns)),
        "feature_mode": feature_mode,
    }


def evaluate_model_pair(
    dataset_path: str | Path,
    *,
    baseline_model_path: str | Path = "model/random_forest.joblib",
    experimental_model_path: str | Path = EXPERIMENTAL_MODEL_PATH,
) -> dict[str, dict[str, object]]:
    """Evaluate production and experimental models on the same random and domain splits."""
    dataset = load_dataset(dataset_path)
    random_train, random_test = train_test_split(
        dataset,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=dataset["label"],
    )
    domain_split = domain_disjoint_split(dataset_path, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    baseline_bundle = joblib.load(Path(baseline_model_path))
    experimental_bundle = joblib.load(Path(experimental_model_path))

    results: dict[str, dict[str, object]] = {}
    for name, train_rows, test_rows in (
        ("random_split_benchmark", random_train, random_test),
        ("domain_disjoint_benchmark", domain_split.train, domain_split.test),
    ):
        results[name] = {}
        for model_name, bundle in (("baseline", baseline_bundle), ("experimental", experimental_bundle)):
            feature_mode = bundle.get("feature_mode", "baseline")
            feature_builder = _baseline_feature_frame if feature_mode == "baseline" else _experimental_feature_frame
            model = RandomForestClassifier(n_estimators=200, random_state=RANDOM_STATE)
            model.fit(feature_builder(train_rows["url"]), train_rows["label"])
            predictions = model.predict(feature_builder(test_rows["url"]))
            results[name][model_name] = _dataset_metrics(test_rows["label"], pd.Series(predictions))

    return results


def evaluate_hard_cases(
    hard_case_path: str | Path,
    *,
    baseline_model_path: str | Path = "model/random_forest.joblib",
    experimental_model_path: str | Path = EXPERIMENTAL_MODEL_PATH,
) -> dict[str, dict[str, object]]:
    """Evaluate the current baseline and experimental model on a documented hard-case suite."""
    cases = pd.read_csv(hard_case_path)
    baseline_bundle = joblib.load(Path(baseline_model_path))
    experimental_bundle = joblib.load(Path(experimental_model_path))
    results: dict[str, dict[str, object]] = {}

    for model_name, bundle in (("baseline", baseline_bundle), ("experimental", experimental_bundle)):
        feature_names = list(bundle["feature_names"])
        feature_mode = bundle.get("feature_mode", "baseline")
        features = pd.DataFrame(
            [extract_features(url, include_experimental=(feature_mode == "experimental")) for url in cases["url"]]
        )
        features = features.reindex(columns=feature_names, fill_value=0)
        predictions = pd.Series(bundle["model"].predict(features))
        results[model_name] = _dataset_metrics(cases["label"], predictions)
    return results


def run_experiment(
    dataset_path: str | Path = "data/raw/urls.csv",
    hard_case_path: str | Path = "data/hard_case_suite.csv",
) -> dict[str, object]:
    """Train the experimental model and evaluate both models against the required suites."""
    baseline_bundle = joblib.load(Path("model/random_forest.joblib"))
    experimental = train_experimental_model(dataset_path, feature_mode="experimental")
    dataset_results = evaluate_model_pair(dataset_path)
    hard_case_results = evaluate_hard_cases(hard_case_path)
    report = {
        "dataset_quality": analyze_dataset(dataset_path),
        "baseline_model": baseline_bundle["feature_names"],
        "experimental_model": experimental,
        "random_split_benchmark": dataset_results["random_split_benchmark"],
        "domain_disjoint_benchmark": dataset_results["domain_disjoint_benchmark"],
        "hard_case_suite": hard_case_results,
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("data/raw/urls.csv"))
    parser.add_argument("--hard-cases", type=Path, default=Path("data/hard_case_suite.csv"))
    parser.add_argument("--output", type=Path, default=REPORT_DIR / "experiment.json")
    arguments = parser.parse_args()

    report = run_experiment(arguments.dataset, arguments.hard_cases)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "experimental_model": report["experimental_model"],
        "random_split_benchmark": report["random_split_benchmark"],
        "domain_disjoint_benchmark": report["domain_disjoint_benchmark"],
        "hard_case_suite": report["hard_case_suite"],
    }, indent=2))


if __name__ == "__main__":
    main()
