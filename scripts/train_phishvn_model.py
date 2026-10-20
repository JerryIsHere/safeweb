"""Train SafeWeb on PhishVN's official grouped partitions and evaluate its test set."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import zipfile
from urllib.parse import urlsplit

import joblib
import matplotlib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, precision_recall_curve
import tldextract

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_extractor import PHISHVN_FEATURE_NAMES, extract_features
from src.evaluate import measure_classifier
from src.predict import DEFAULT_MODEL_PATH
from src.train import model_suite
from src.url_validation import validate_url
DATASET_PATH = PROJECT_ROOT / "data" / "processed" / "phishvn_clean.csv"
DATABASE_PATH = PROJECT_ROOT / "data" / "phishvn_database.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "phishvn_domain_eval.json"
METRICS_PATH = PROJECT_ROOT / "reports" / "metrics.json"
PHIUSIIL_PATH = PROJECT_ROOT / "data" / "raw" / "phiusiil+phishing+url+dataset.zip"
_DOMAIN_PARSER = tldextract.TLDExtract(suffix_list_urls=())


def _registrable_domain(url: str) -> str:
    host = (urlsplit(url).hostname or "").lower()
    extracted = _DOMAIN_PARSER(host)
    return extracted.top_domain_under_public_suffix or host


def prepare_phiusiil_training_rows(
    frame: pd.DataFrame,
    excluded_domains: set[str],
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Normalize PhiUSIIL labels/URLs and remove ambiguous or held-out domains."""
    if not {"URL", "label"}.issubset(frame.columns):
        raise ValueError("PhiUSIIL data must contain URL and label columns.")
    labels = pd.to_numeric(frame["label"], errors="coerce")
    if labels.isna().any() or not set(labels.unique()).issubset({0, 1}):
        raise ValueError("PhiUSIIL labels must be binary 0/1 values.")

    normalized_urls = []
    valid_indexes = []
    for index, value in frame["URL"].items():
        try:
            normalized_urls.append(validate_url(str(value)))
            valid_indexes.append(index)
        except ValueError:
            continue
    prepared = pd.DataFrame(
        {
            "url": normalized_urls,
            "label": (1 - labels.loc[valid_indexes].astype(int)).to_numpy(),
        }
    )
    prepared["url_key"] = prepared["url"].map(
        lambda url: (
            lambda parts: f"{parts.netloc.lower()}{parts.path.rstrip('/')}?{parts.query}".rstrip("?")
        )(urlsplit(url))
    )
    invalid_url_rows = len(frame) - len(prepared)
    conflict_mask = prepared.groupby("url_key")["label"].transform("nunique").gt(1)
    conflicting_url_rows = int(conflict_mask.sum())
    prepared = prepared.loc[~conflict_mask].drop_duplicates("url_key", keep="first").drop(columns="url_key").copy()
    duplicate_url_rows = len(frame) - invalid_url_rows - conflicting_url_rows - len(prepared)
    prepared["registrable_domain"] = prepared["url"].map(_registrable_domain)
    test_domain_mask = prepared["registrable_domain"].isin(excluded_domains)
    excluded_test_domain_rows = int(test_domain_mask.sum())
    prepared = prepared.loc[~test_domain_mask].drop(columns="registrable_domain").reset_index(drop=True)
    summary: dict[str, object] = {
        "source_rows": int(len(frame)),
        "invalid_url_rows_removed": invalid_url_rows,
        "conflicting_url_rows_removed": conflicting_url_rows,
        "duplicate_url_rows_removed": duplicate_url_rows,
        "excluded_domain_rows_removed": excluded_test_domain_rows,
        "excluded_domains": len(excluded_domains),
        "training_rows": int(len(prepared)),
        "training_labels": {
            "benign": int((prepared["label"] == 0).sum()),
            "phishing": int((prepared["label"] == 1).sum()),
        },
    }
    return prepared, summary


def load_phiusiil_archive(path: Path = PHIUSIIL_PATH) -> pd.DataFrame:
    """Read the URL and label columns from the supplied PhiUSIIL ZIP archive."""
    with zipfile.ZipFile(path) as archive:
        csv_members = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(csv_members) != 1:
            raise ValueError("PhiUSIIL archive must contain exactly one CSV file.")
        with archive.open(csv_members[0]) as source:
            return pd.read_csv(source, usecols=["URL", "label"], low_memory=False)


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
        host = (urlsplit(url).hostname or "").lower().removeprefix("www.")
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
    return features


def build_url_feature_frame(
    urls: pd.Series,
    database: dict[str, object],
    feature_names: list[str],
) -> pd.DataFrame:
    """Build the shared URL feature schema for sources without precomputed fields."""
    profiles = database.get("hostProfiles", {})
    profile_fields = database.get("hostProfileFields", [])
    suspicious_tlds = set(database.get("suspiciousTlds", []))
    values = []
    for url in urls:
        host = (urlsplit(url).hostname or "").lower().removeprefix("www.")
        profile_values = profiles.get(host)
        profile = dict(zip(profile_fields, profile_values, strict=True)) if profile_values else None
        values.append(
            extract_features(
                url,
                domain_profile=profile,
                suspicious_tlds=suspicious_tlds,
            )
        )
    return pd.DataFrame(values, index=urls.index).reindex(columns=feature_names)


def source_balanced_sample_weights(
    phishvn_labels: pd.Series,
    phiusiil_labels: pd.Series,
) -> np.ndarray:
    """Give both source datasets equal total weight and equal class weight."""
    labels = np.concatenate(
        [phishvn_labels.to_numpy(dtype=int), phiusiil_labels.to_numpy(dtype=int)]
    )
    source_ids = np.concatenate(
        [np.zeros(len(phishvn_labels), dtype=int), np.ones(len(phiusiil_labels), dtype=int)]
    )
    weights = np.zeros(len(labels), dtype=float)
    for source_id in (0, 1):
        source_mask = source_ids == source_id
        for label in (0, 1):
            class_mask = source_mask & (labels == label)
            class_count = int(class_mask.sum())
            if class_count == 0:
                raise ValueError("Each source must contain both benign and phishing rows.")
            weights[class_mask] = 1.0 / (4 * class_count)
    return weights * (len(weights) / weights.sum())


def fit_classifier(model, features: pd.DataFrame, labels: pd.Series, sample_weights: np.ndarray) -> None:
    """Fit supported estimators/pipelines with the shared source-balanced weights."""
    if hasattr(model, "steps"):
        model.fit(features, labels, sample_weight=sample_weights)
    else:
        model.fit(features, labels, sample_weight=sample_weights)


def select_f1_threshold(labels: pd.Series, probabilities: np.ndarray) -> float:
    """Select the phishing-probability threshold maximizing validation F1."""
    precision, recall, thresholds = precision_recall_curve(labels, probabilities)
    if not len(thresholds):
        raise ValueError("Validation data must contain both classes to select a threshold.")
    f1_scores = 2 * precision[:-1] * recall[:-1] / np.maximum(precision[:-1] + recall[:-1], 1e-12)
    best_indexes = np.flatnonzero(f1_scores == f1_scores.max())
    best_index = max(best_indexes, key=lambda index: (precision[index], thresholds[index]))
    return float(thresholds[best_index])


def main() -> None:
    dataset = pd.read_csv(DATASET_PATH, low_memory=False)
    database = json.loads(DATABASE_PATH.read_text(encoding="utf-8"))
    train_frame = dataset[dataset["split"] == "train"].copy()
    validation_frame = dataset[dataset["split"] == "val"].copy()
    test_frame = dataset[dataset["split"] == "test"].copy()
    if train_frame.empty or validation_frame.empty or test_frame.empty:
        raise ValueError("The cleaned dataset must include train, val, and test partitions.")
    phishvn_train_features = build_feature_frame(train_frame, database)
    X_validation = build_feature_frame(validation_frame, database)
    y_validation = validation_frame["label"].astype(int)
    X_test = build_feature_frame(test_frame, database)
    y_test = test_frame["label"].astype(int)

    heldout_domains = {
        _registrable_domain(url)
        for url in pd.concat([validation_frame["url"], test_frame["url"]], ignore_index=True)
    }
    phiusiil_raw = load_phiusiil_archive()
    phiusiil_frame, phiusiil_audit = prepare_phiusiil_training_rows(phiusiil_raw, heldout_domains)
    if phiusiil_frame["label"].nunique() != 2:
        raise ValueError("PhiUSIIL training rows must contain both benign and phishing labels.")
    feature_names = list(phishvn_train_features.columns)
    phiusiil_features = build_url_feature_frame(phiusiil_frame["url"], database, feature_names)
    X_train = pd.concat([phishvn_train_features, phiusiil_features], ignore_index=True)
    y_train = pd.concat(
        [train_frame["label"].astype(int).reset_index(drop=True), phiusiil_frame["label"]],
        ignore_index=True,
    )
    sample_weights = source_balanced_sample_weights(
        train_frame["label"].astype(int).reset_index(drop=True),
        phiusiil_frame["label"],
    )

    model_paths = {
        "random_forest": DEFAULT_MODEL_PATH,
        "gradient_boosting": PROJECT_ROOT / "model" / "gradient_boosting.joblib",
        "svm": PROJECT_ROOT / "model" / "svm.joblib",
        "logistic_regression": PROJECT_ROOT / "model" / "logistic_regression.joblib",
    }
    evaluations = {}
    validation_evaluations = {}
    report_sections = [
        "PhishVN v3.1.0 official domain-disjoint test partition",
        f"Training rows: {len(X_train)} (PhishVN: {len(train_frame)}, PhiUSIIL: {len(phiusiil_frame)}) | Validation rows: {len(validation_frame)} | Test rows: {len(test_frame)}",
    ]
    for name, model in model_suite().items():
        fit_classifier(model, X_train, y_train, sample_weights)
        decision_threshold = None
        if name == "svm":
            classes = list(model.classes_)
            validation_probabilities = model.predict_proba(X_validation)[:, classes.index(1)]
            decision_threshold = select_f1_threshold(y_validation, validation_probabilities)
            validation_evaluations[name] = measure_classifier(
                model,
                X_validation,
                y_validation,
                decision_threshold=decision_threshold,
            )
        evaluations[name] = measure_classifier(
            model,
            X_test,
            y_test,
            len(X_train),
            decision_threshold=decision_threshold,
        )
        model_paths[name].parent.mkdir(parents=True, exist_ok=True)
        bundle = {"model": model, "feature_names": feature_names}
        if decision_threshold is not None:
            bundle["decision_threshold"] = decision_threshold
        joblib.dump(bundle, model_paths[name])
        test_predictions = (
            model.predict(X_test)
            if decision_threshold is None
            else (
                model.predict_proba(X_test)[:, list(model.classes_).index(1)]
                >= decision_threshold
            ).astype(int)
        )
        report_sections.extend(
            [
                "",
                name.replace("_", " ").title(),
                *(
                    [f"Validation-selected decision threshold: {decision_threshold:.6f}"]
                    if decision_threshold is not None else []
                ),
                classification_report(
                    y_test,
                    test_predictions,
                    labels=[0, 1],
                    target_names=["benign", "phishing"],
                    zero_division=0,
                ).rstrip(),
            ]
        )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "dataset": str(DATASET_PATH),
        "dataset_source": ["PhishVN v3.1.0 open archive", "PhiUSIIL Phishing URL Dataset"],
        "split": "phishvn_official_grouped_temporal_train_val_test; phiusiil_excludes_validation_and_test_domain_overlap",
        "train_rows": int(len(X_train)),
        "phishvn_train_rows": int(len(train_frame)),
        "phiusiil_train_rows": int(len(phiusiil_frame)),
        "phiusiil_audit": phiusiil_audit,
        "training_weighting": "equal total weight per source and equal benign/phishing weight within source",
        "test_rows": int(len(test_frame)),
        "validation_rows": int(len(validation_frame)),
        "feature_count": len(feature_names),
        "features": feature_names,
        "pre_extracted_comp_phish_features_used": 0,
        "phishvn_source_feature_columns_recomputed": len(PHISHVN_FEATURE_NAMES),
        "test_domains_disjoint_from_training": True,
        "train_labels": {"benign": int((y_train == 0).sum()), "phishing": int((y_train == 1).sum())},
        "test_labels": {"benign": int((y_test == 0).sum()), "phishing": int((y_test == 1).sum())},
        "evaluations": evaluations,
        "validation_evaluations": validation_evaluations,
        "selected_model": "random_forest",
    }
    REPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    METRICS_PATH.write_text(
        json.dumps(
            {
                "dataset_source": ["PhishVN v3.1.0 open archive", "PhiUSIIL Phishing URL Dataset"],
                "evaluations": evaluations,
                "train_rows": int(len(X_train)),
                "phishvn_train_rows": int(len(train_frame)),
                "phiusiil_train_rows": int(len(phiusiil_frame)),
                "phiusiil_audit": phiusiil_audit,
                "training_weighting": "equal total weight per source and equal benign/phishing weight within source",
                "test_rows": int(len(test_frame)),
                "validation_rows": int(len(validation_frame)),
                "validation_evaluations": validation_evaluations,
                "pre_extracted_comp_phish_features_used": 0,
                "phishvn_source_feature_columns_recomputed": len(PHISHVN_FEATURE_NAMES),
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
    print(
        json.dumps(
            {
                "selected_model": "random_forest",
                "phishvn_train_rows": int(len(train_frame)),
                "phiusiil_audit": phiusiil_audit,
                "test_rows": int(len(test_frame)),
                "evaluations": evaluations,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
