from src.feature_extractor import extract_features
from src.predict import predict_url


class FixedModel:
    classes_ = [0, 1]

    def predict_proba(self, features):
        return [[0.2, 0.8]]

    def predict(self, features):
        return [1]


def test_prediction_without_artifact_returns_unloaded_state(tmp_path) -> None:
    result = predict_url("https://example.com/login", model_path=tmp_path / "missing.joblib")

    assert result["status"] == "model_not_loaded"
    assert result["prediction"] is None
    assert result["probability"] is None
    assert result["risk_level"] is None
    assert result["features"]["keyword_login"] == 1
    assert result["explanations"]


def test_prediction_uses_loaded_bundle_without_creating_model_file() -> None:
    bundle = {
        "model": FixedModel(),
        "feature_names": list(extract_features("https://example.com")),
    }

    result = predict_url("https://example.com/login", bundle=bundle)

    assert result["status"] == "ok"
    assert result["prediction"] == "phishing"
    assert result["probability"] == 0.8
    assert result["risk_level"] == "VERY HIGH"


def test_risk_levels_follow_the_explicit_score_scale() -> None:
    from src.config import risk_level

    assert risk_level(0.20) == "LOW"
    assert risk_level(0.30) == "CAUTION"
    assert risk_level(0.60) == "HIGH"
    assert risk_level(0.80) == "VERY HIGH"


def test_prediction_rejects_empty_or_invalid_url() -> None:
    for url in ("", "ftp://example.com", "http://[broken"):
        try:
            predict_url(url, bundle={})
        except ValueError:
            continue
        raise AssertionError(f"Expected invalid URL to be rejected: {url!r}")


def test_relative_model_path_is_resolved_from_project_root(monkeypatch) -> None:
    from src.predict import PROJECT_ROOT, configured_model_path

    monkeypatch.setenv("SAFEWEB_MODEL_PATH", "artifacts/model.joblib")

    assert configured_model_path() == PROJECT_ROOT / "artifacts" / "model.joblib"