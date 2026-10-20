"""Export the trained Random Forest and offline suffix rules for browser inference."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_extractor import _DOMAIN_PARSER
from src.predict import DEFAULT_DATABASE_PATH, DEFAULT_MODEL_PATH, load_model, load_phishvn_database
from src.url_intelligence import classify_url
from src.url_validation import normalize_url


DEFAULT_OUTPUT = PROJECT_ROOT / "web" / "static" / "model-data.js"
DEFAULT_RECORDS_OUTPUT = PROJECT_ROOT / "web" / "static" / "database-records.json"


def _ascii_rule(rule: str) -> str:
    prefix = ""
    suffix = rule
    if suffix.startswith("!"):
        prefix, suffix = "!", suffix[1:]
    elif suffix.startswith("*."):
        prefix, suffix = "*.", suffix[2:]
    labels = [label.encode("idna").decode("ascii") for label in suffix.split(".")]
    return prefix + ".".join(labels).lower()


def _tree_payload(model, feature_names: list[str], probabilities: bool) -> list[dict[str, object]]:
    trees = []
    for estimator in np.asarray(model.estimators_, dtype=object).flat:
        tree = estimator.tree_
        if probabilities:
            values = tree.value[:, 0, :]
            totals = values.sum(axis=1)
            outcomes = np.divide(
                values[:, 1], totals, out=np.zeros_like(totals), where=totals != 0
            ).tolist()
        else:
            outcomes = tree.value[:, 0, 0].tolist()
        trees.append(
            {
                "left": tree.children_left.tolist(),
                "right": tree.children_right.tolist(),
                "feature": tree.feature.tolist(),
                "threshold": tree.threshold.tolist(),
                "output": outcomes,
            }
        )
    return trees


def _scale_payload(pipeline, classifier_name: str) -> dict[str, object]:
    scaler = pipeline.named_steps["standardscaler"]
    classifier = pipeline.named_steps[classifier_name]
    return {
        "mean": scaler.mean_.tolist(),
        "scale": scaler.scale_.tolist(),
        "coefficients": classifier.coef_[0].tolist(),
        "intercept": float(classifier.intercept_[0]),
    }


def _export_models(model_paths: dict[str, Path]) -> tuple[list[str], dict[str, object]]:
    bundles = {name: load_model(path) for name, path in model_paths.items()}
    features = bundles["random_forest"]["feature_names"]
    exported: dict[str, object] = {}
    for name, bundle in bundles.items():
        if bundle["feature_names"] != features:
            raise ValueError(f"{name} model feature schema does not match Random Forest.")
        model = bundle["model"]
        if [int(value) for value in model.classes_] != [0, 1]:
            raise ValueError(f"{name} model classes must be [0, 1].")
        if name == "random_forest":
            exported[name] = {"trees": _tree_payload(model, features, probabilities=True)}
        elif name == "gradient_boosting":
            prior = model.init_.class_prior_
            exported[name] = {
                "trees": _tree_payload(model, features, probabilities=False),
                "learningRate": model.learning_rate,
                "initialRawScore": float(np.log(prior[1] / prior[0])),
            }
        elif name == "logistic_regression":
            exported[name] = _scale_payload(model, "logisticregression")
        elif name == "svm":
            calibrated = model.calibrated_classifiers_[0]
            calibrator = calibrated.calibrators[0]
            exported[name] = {
                **_scale_payload(calibrated.estimator, "linearsvc"),
                "calibrationA": float(calibrator.a_),
                "calibrationB": float(calibrator.b_),
                "decisionThreshold": float(bundle.get("decision_threshold", 0.5)),
            }
    return features, exported


def export_database_records(output_path: Path) -> int:
    """Write the normalized PhishVN rows required by the explorer and verdict UI."""
    frame = pd.read_csv(PROJECT_ROOT / "data" / "processed" / "phishvn_clean.csv", low_memory=False)
    records = []
    categories: dict[str, str] = {}
    for row in frame.itertuples(index=False):
        values = row._asdict()
        url = str(values["url"])
        parts = urlsplit(normalize_url(url, strip_www=True))
        brand_hint = "" if pd.isna(values.get("impersonated_org")) else str(values["impersonated_org"])
        intelligence = classify_url(
            url,
            scenario=str(values.get("scenario", "")),
            impersonated_brand=brand_hint,
        )
        category_id = intelligence["category_id"]
        categories[category_id] = intelligence["category"]
        records.append(
            [
                url,
                int(values["label"]),
                "" if pd.isna(values.get("collected_at")) else str(values["collected_at"]),
                "" if pd.isna(values.get("tier")) else str(values["tier"]).lower(),
                category_id,
                intelligence["provider"],
                intelligence["brand"],
                int(values["phishvn_url_len"]),
                int(values["phishvn_subdom_cnt"]),
                int(values["phishvn_is_ip"]),
                int(values["suspicious_tld"]),
                round(float(values["phishvn_entropy"]), 3),
            ]
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {
                "source": "PhishVN v3.1.0",
                "citation": "Thai Nguyen Vu, PhishVN v3.1.0 (2026), DOI 10.17632/b97hxbxtpd.4",
                "license": "CC BY 4.0",
                "categories": categories,
                "records": records,
            },
            separators=(",", ":"),
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )
    return output_path.stat().st_size


def export_browser_model(model_path: Path, output_path: Path) -> int:
    """Write exact browser inference parameters and offline PhishVN resources."""
    model_paths = {
        "random_forest": model_path,
        "gradient_boosting": model_path.with_name("gradient_boosting.joblib"),
        "svm": model_path.with_name("svm.joblib"),
        "logistic_regression": model_path.with_name("logistic_regression.joblib"),
    }
    features, models = _export_models(model_paths)
    suffix_rules = sorted({_ascii_rule(rule) for rule in _DOMAIN_PARSER.tlds})
    payload = {
        "features": features,
        "models": models,
        "trees": models["random_forest"]["trees"],
        "publicSuffixRules": suffix_rules,
        "phishvnDatabase": load_phishvn_database(str(DEFAULT_DATABASE_PATH)),
    }
    javascript = "globalThis.safewebModel = " + json.dumps(
        payload, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ) + ";\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(javascript, encoding="utf-8")
    return output_path.stat().st_size


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH,
                        help="Random Forest artifact; companion model artifacts are loaded beside it")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--records-output", type=Path, default=DEFAULT_RECORDS_OUTPUT)
    arguments = parser.parse_args()
    size = export_browser_model(arguments.model, arguments.output)
    print(f"Exported browser model to {arguments.output} ({size:,} bytes).")
    records_size = export_database_records(arguments.records_output)
    print(f"Exported PhishVN records to {arguments.records_output} ({records_size:,} bytes).")


if __name__ == "__main__":
    main()