"""Evaluate a saved model once on the reproducible held-out test partition."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

from src.data_loader import load_dataset
from src.predict import DEFAULT_MODEL_PATH, load_model
from src.train import RANDOM_STATE, TEST_SIZE, feature_frame


def evaluate_model(
    dataset_path: str | Path,
    model_path: str | Path = DEFAULT_MODEL_PATH,
    report_dir: str | Path = "reports",
) -> dict[str, object]:
    """Generate standard metrics and error-analysis artifacts for held-out data."""
    dataset = load_dataset(dataset_path)
    _, test_rows = train_test_split(
        dataset,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=dataset["label"],
    )
    test_features = feature_frame(test_rows["url"])
    test_labels = test_rows["label"]
    bundle = load_model(model_path)
    model = bundle["model"]
    predictions = model.predict(test_features)
    matrix = confusion_matrix(test_labels, predictions, labels=[0, 1])
    metrics: dict[str, object] = {
        "accuracy": float(accuracy_score(test_labels, predictions)),
        "precision": float(precision_score(test_labels, predictions, zero_division=0)),
        "recall": float(recall_score(test_labels, predictions, zero_division=0)),
        "f1_score": float(f1_score(test_labels, predictions, zero_division=0)),
        "confusion_matrix_labels": ["legitimate", "phishing"],
        "confusion_matrix": matrix.tolist(),
        "classification_report": classification_report(
            test_labels,
            predictions,
            labels=[0, 1],
            target_names=["legitimate", "phishing"],
            output_dict=True,
            zero_division=0,
        ),
        "test_rows": int(len(test_labels)),
    }
    output = Path(report_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (output / "classification_report.txt").write_text(
        classification_report(
            test_labels,
            predictions,
            labels=[0, 1],
            target_names=["legitimate", "phishing"],
            zero_division=0,
        ),
        encoding="utf-8",
    )
    errors = test_rows.loc[:, ["url", "label"]].copy()
    errors["prediction"] = predictions
    errors["error_type"] = "correct"
    errors.loc[(errors.label == 1) & (errors.prediction == 1), "error_type"] = "true_positive"
    errors.loc[(errors.label == 0) & (errors.prediction == 0), "error_type"] = "true_negative"
    errors.loc[(errors.label == 0) & (errors.prediction == 1), "error_type"] = "false_positive"
    errors.loc[(errors.label == 1) & (errors.prediction == 0), "error_type"] = "false_negative"
    errors.to_csv(output / "error_analysis.csv", index=False)

    figure, axis = plt.subplots()
    axis.imshow(matrix, cmap="Blues")
    axis.set(xticks=[0, 1], yticks=[0, 1], xticklabels=["Legitimate", "Phishing"],
             yticklabels=["Legitimate", "Phishing"], xlabel="Predicted", ylabel="Actual")
    for (row, column), value in np.ndenumerate(matrix):
        axis.text(column, row, str(value), ha="center", va="center")
    figure.tight_layout()
    figure.savefig(output / "confusion_matrix.png", dpi=160)
    plt.close(figure)

    if hasattr(model, "feature_importances_"):
        importance = pd.Series(model.feature_importances_, index=bundle["feature_names"])
        importance.sort_values().plot.barh(figsize=(8, 7), color="#187c72")
        plt.xlabel("Feature importance")
        plt.tight_layout()
        plt.savefig(output / "feature_importance.png", dpi=160)
        plt.close()
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--reports", type=Path, default=Path("reports"))
    arguments = parser.parse_args()
    results = evaluate_model(arguments.dataset, arguments.model, arguments.reports)
    print(json.dumps({key: results[key] for key in ("accuracy", "precision", "recall", "f1_score")}, indent=2))


if __name__ == "__main__":
    main()