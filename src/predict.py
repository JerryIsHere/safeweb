"""Load a trained model and assess a URL string."""

from pathlib import Path
from functools import lru_cache
import json
import os
from typing import Any
from urllib.parse import urlsplit

import joblib
import pandas as pd

from src.config import RiskThresholds, risk_level
from src.explain import explain_features
from src.feature_extractor import extract_features
from src.url_intelligence import detect_brand_impersonation
from src.url_validation import normalize_url, validate_url


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "model" / "random_forest.joblib"
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "phishvn_database.json"


def _zero_model_consensus() -> dict[str, dict[str, str | float]]:
    return {
        "random_forest": {"prediction": "legitimate", "probability": 0.0, "risk_level": "LOW"},
        "gradient_boosting": {"prediction": "legitimate", "probability": 0.0, "risk_level": "LOW"},
        "svm": {"prediction": "legitimate", "probability": 0.0, "risk_level": "LOW"},
        "logistic_regression": {"prediction": "legitimate", "probability": 0.0, "risk_level": "LOW"},
    }


@lru_cache(maxsize=2)
def load_phishvn_database(path: str = str(DEFAULT_DATABASE_PATH)) -> dict[str, Any]:
    """Load the compact PhishVN URL/host/signature index when available."""
    database_path = Path(path)
    if not database_path.is_file():
        return {}
    return json.loads(database_path.read_text(encoding="utf-8"))


def _database_url_key(url: str) -> str:
    parts = urlsplit(normalize_url(url, strip_www=True))
    return f"{parts.netloc.lower()}{parts.path.rstrip('/')}?{parts.query}".rstrip("?")


def _profile_for_host(host: str, database: dict[str, Any]) -> dict[str, int | float] | None:
    values = database.get("hostProfiles", {}).get(host)
    fields = database.get("hostProfileFields", [])
    return dict(zip(fields, values, strict=True)) if values is not None else None


def _database_match(url: str, features: dict[str, int | float], database: dict[str, Any]) -> dict[str, Any]:
    if not database:
        return {"matched": False, "type": None, "provenance": None}
    key = _database_url_key(url)
    host = (urlsplit(url).hostname or "").lower().removeprefix("www.")
    if key in set(database.get("knownPhishingUrlKeys", [])):
        match_type = "exact_url"
    elif host in {value.removeprefix("www.") for value in database.get("knownPhishingHosts", [])}:
        match_type = "known_phishing_host"
    else:
        signature_names = database.get("signatureFeatureNames", [])
        signature_values = [
            features.get(name, features.get(f"phishvn_{name}", 0))
            for name in signature_names
        ]
        signature = ",".join(f"{float(value):.5f}" for value in signature_values)
        if signature not in set(database.get("knownPhishingFeatureSignatures", [])):
            return {"matched": False, "type": None, "provenance": None}
        match_type = "feature_signature"
    return {
        "matched": True,
        "type": match_type,
        "provenance": "Matched in reference database",
    }


def configured_model_path() -> Path:
    """Return the model path from the environment or the portable project default."""
    configured_path = os.getenv("SAFEWEB_MODEL_PATH")
    if not configured_path:
        return DEFAULT_MODEL_PATH
    path = Path(configured_path).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_model(model_path: str | Path = DEFAULT_MODEL_PATH) -> dict[str, Any]:
    """Load and minimally validate a saved SafeWeb model bundle."""
    bundle = joblib.load(model_path)
    if (
        not isinstance(bundle, dict)
        or "model" not in bundle
        or "feature_names" not in bundle
    ):
        raise ValueError("Model artifact is not a SafeWeb model bundle.")
    feature_names = bundle["feature_names"]
    model = bundle["model"]
    if (
        not isinstance(feature_names, list)
        or not feature_names
        or not all(isinstance(name, str) for name in feature_names)
        or len(set(feature_names)) != len(feature_names)
        or not hasattr(model, "classes_")
        or not hasattr(model, "predict")
        or not hasattr(model, "predict_proba")
        or not {0, 1}.issubset(set(model.classes_))
    ):
        raise ValueError("Model artifact is missing required SafeWeb model fields.")
    return bundle


def predict_url(
    url: str,
    bundle: dict[str, Any] | None = None,
    thresholds: RiskThresholds | None = None,
    model_path: str | Path | None = None,
) -> dict[str, Any]:
    """Return a model assessment or explicit no-model state without network access."""
    normalized_url = validate_url(url)
    database = load_phishvn_database()
    parsed_url = urlsplit(normalized_url)
    host = (parsed_url.hostname or "").lower().removeprefix("www.")
    is_vietnamese_government_domain = (
        not (parsed_url.username or parsed_url.password)
        and (host == "gov.vn" or host.endswith(".gov.vn"))
    )
    features = extract_features(
        normalized_url,
        domain_profile=_profile_for_host(host, database),
        suspicious_tlds=set(database.get("suspiciousTlds", [])),
    )
    database_match = _database_match(normalized_url, features, database)
    impersonated_brand = detect_brand_impersonation(normalized_url)
    explanations = explain_features(features)
    if impersonated_brand:
        explanations.insert(0, f"Potential brand lookalike detected: {impersonated_brand}.")
    if is_vietnamese_government_domain:
        explanations.insert(0, "Official Vietnamese government domain (.gov.vn) recognized.")

    if is_vietnamese_government_domain or database_match["matched"] or impersonated_brand:
        if is_vietnamese_government_domain:
            prediction = "legitimate"
            risk_level_value = "LOW"
            bypass_reason = "gov_vn"
            explanations.insert(0, "Custom rule applied: official Vietnamese government domain (.gov.vn).")
        elif database_match["matched"]:
            prediction = "phishing"
            risk_level_value = "VERY HIGH"
            bypass_reason = "database_match"
            explanations.insert(0, "Custom rule applied: matched in reference database.")
        else:
            prediction = "phishing"
            risk_level_value = "VERY HIGH"
            bypass_reason = "brand_rule"
            explanations.insert(0, f"Custom rule applied: potential brand lookalike ({impersonated_brand}).")
        return {
            "status": "ok",
            "prediction": prediction,
            "probability": 0.0,
            "risk_level": risk_level_value,
            "models": _zero_model_consensus(),
            "model_ensemble": {"prediction": "legitimate", "probability": 0.0, "risk_level": "LOW"},
            "model_consensus_bypassed": True,
            "model_consensus_bypass_reason": bypass_reason,
            "features": features,
            "database_match": database_match,
            "brand_impersonation": impersonated_brand,
            "verification_stages": {
                "database": "matched" if database_match["matched"] else "checked_no_match",
                "machine_learning": "bypassed",
            },
            "explanations": explanations,
            "disclaimer": "This is a dataset-backed risk assessment, not proof that a destination is safe or malicious.",
        }

    selected_model_path = Path(model_path) if model_path is not None else configured_model_path()
    if bundle is None:
        if not selected_model_path.is_file():
            return {
                "status": "model_not_loaded",
                "prediction": None,
                "probability": None,
                "risk_level": None,
                "features": features,
                "database_match": database_match,
                "brand_impersonation": impersonated_brand,
                "explanations": explanations,
            }
        bundle = load_model(selected_model_path)

    feature_names = bundle["feature_names"]
    if any(name not in features for name in feature_names):
        raise ValueError("Model artifact expects unsupported URL features.")
    row = pd.DataFrame([{name: features[name] for name in feature_names}])
    model = bundle["model"]
    classes = list(model.classes_)
    probability = float(model.predict_proba(row)[0][classes.index(1)])
    decision_threshold = bundle.get("decision_threshold")
    predicted_label = (
        int(probability >= float(decision_threshold))
        if decision_threshold is not None
        else int(model.predict(row)[0])
    )
    level = risk_level(probability, thresholds)
    return {
        "status": "ok",
        "prediction": "phishing" if predicted_label == 1 else "legitimate",
        "probability": probability,
        "risk_level": level,
        "models": {},
        "model_ensemble": {
            "prediction": "phishing" if predicted_label == 1 else "legitimate",
            "probability": probability,
            "risk_level": level,
        },
        "model_consensus_bypassed": False,
        "model_consensus_bypass_reason": None,
        "features": features,
        "database_match": database_match,
        "brand_impersonation": impersonated_brand,
        "verification_stages": {
            "database": "matched" if database_match["matched"] else "checked_no_match",
            "machine_learning": "evaluated",
        },
        "explanations": explanations,
        "disclaimer": "This is a dataset-backed risk assessment, not proof that a destination is safe or malicious.",
    }