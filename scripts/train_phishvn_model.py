"""Train SafeWeb on PhishVN's official grouped partitions and evaluate its test set."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

import joblib
import matplotlib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_extractor import PHISHVN_FEATURE_NAMES, extract_features
from src.evaluate import measure_classifier
from src.predict import DEFAULT_MODEL_PATH
from src.train import model_suite
DATASET_PATH = PROJECT_ROOT / "data" / "processed" / "phishvn_clean.csv"
DATABASE_PATH = PROJECT_ROOT / "data" / "phishvn_database.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "phishvn_domain_eval.json"
METRICS_PATH = PROJECT_ROOT / "reports" / "metrics.json"
SOURCE_FEATURE_NAMES = tuple(name.removeprefix("phishvn_") for name in PHISHVN_FEATURE_NAMES)


def save_confusion_matrices(evaluations: dict[str, dict[str, object]]) -> None:
    figure, axes = plt.subplots(2, 2, figsize=(10, 8))
    for axis, (name, evaluation) in zip(axes.flat, evaluations.items(), strict=True):
        matrix = np.asarray(evaluation["confusion_matrix"])
        axis.imshow(matrix, cmap="Blues")
        axis.set(
            title=name.replace("_", " ").title(),
            xticks=[0, 1],
            yticks=[0, 1],
            xticklabels=["Benign", "Phishing"],
            yticklabels=["Benign", "Phishing"],
            xlabel="Predicted",
            ylabel="Actual",
        )
        for (row, column), value in np.ndenumerate(matrix):
            axis.text(column, row, str(value), ha="center", va="center")
    figure.tight_layout()
    figure.savefig(PROJECT_ROOT / "reports" / "confusion_matrix.png", dpi=160)
    plt.close(figure)


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

    feature_names = list(X_train.columns)
    model_paths = {
        "random_forest": DEFAULT_MODEL_PATH,
        "gradient_boosting": PROJECT_ROOT / "model" / "gradient_boosting.joblib",
        "svm": PROJECT_ROOT / "model" / "svm.joblib",
        "logistic_regression": PROJECT_ROOT / "model" / "logistic_regression.joblib",
    }
    evaluations = {}
    report_sections = [
        "PhishVN v3.1.0 official domain-disjoint test partition",
        f"Training rows: {len(train_frame)} | Test rows: {len(test_frame)}",
    ]
    for name, model in model_suite().items():
        model.fit(X_train, y_train)
        evaluations[name] = measure_classifier(model, X_test, y_test, len(train_frame))
        model_paths[name].parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": model, "feature_names": feature_names}, model_paths[name])
        report_sections.extend(
            [
                "",
                name.replace("_", " ").title(),
                classification_report(
                    y_test,
                    model.predict(X_test),
                    labels=[0, 1],
                    target_names=["benign", "phishing"],
                    zero_division=0,
                ).rstrip(),
            ]
        )

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
        "evaluations": evaluations,
        "selected_model": "random_forest",
    }
    REPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    METRICS_PATH.write_text(
        json.dumps(
            {
                "dataset_source": "PhishVN v3.1.0 open archive",
                "evaluations": evaluations,
                "train_rows": int(len(train_frame)),
                "test_rows": int(len(test_frame)),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (PROJECT_ROOT / "reports" / "classification_report.txt").write_text(
        "\n".join(report_sections) + "\n",
        encoding="utf-8",
    )
    save_confusion_matrices(evaluations)
    print(json.dumps({"selected_model": "random_forest", "evaluations": evaluations}, indent=2))


if __name__ == "__main__":
    main()
