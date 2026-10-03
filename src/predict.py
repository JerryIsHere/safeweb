"""Load a trained model and assess a URL string."""

from pathlib import Path
import os
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from src.config import RiskThresholds, risk_level
from src.explain import explain_features
from src.feature_extractor import extract_features
from src.url_validation import validate_url


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "model" / "random_forest.joblib"


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
    features = extract_features(normalized_url)
    selected_model_path = Path(model_path) if model_path is not None else configured_model_path()
    if bundle is None:
        if not selected_model_path.is_file():
            return {
                "status": "model_not_loaded",
                "prediction": None,
                "probability": None,
                "risk_level": None,
                "features": features,
                "explanations": explain_features(features),
            }
        bundle = load_model(selected_model_path)

    feature_names = bundle["feature_names"]
    if any(name not in features for name in feature_names):
        raise ValueError("Model artifact expects unsupported URL features.")
    row = pd.DataFrame([{name: features[name] for name in feature_names}])
    model = bundle["model"]
    classes = list(model.classes_)
    probability = float(model.predict_proba(row)[0][classes.index(1)])
    predicted_label = int(model.predict(row)[0])
    return {
        "status": "ok",
        "prediction": "phishing" if predicted_label == 1 else "legitimate",
        "probability": probability,
        "risk_level": risk_level(probability, thresholds),
        "features": features,
        "explanations": explain_features(features),
        "disclaimer": "This is a model assessment of URL characteristics, not proof of safety or harm.",
    }