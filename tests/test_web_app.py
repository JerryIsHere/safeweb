from src.feature_extractor import extract_features
from web.app import create_app


class FixedModel:
    classes_ = [0, 1]

    def predict_proba(self, features):
        return [[0.13, 0.87]]

    def predict(self, features):
        return [1]


def _bundle():
    return {"model": FixedModel(), "feature_names": list(extract_features("https://example.test"))}


def test_home_page_renders_model_state() -> None:
    response = create_app(model_path="missing-model.joblib").test_client().get("/")

    assert response.status_code == 200
    assert b"MODEL NOT LOADED" in response.data
    assert b"No page is opened, contacted, or downloaded." in response.data


def test_home_page_exposes_language_selection_and_translation_assets() -> None:
    client = create_app(model_path="missing-model.joblib").test_client()
    response = client.get("/")
    translations = client.get("/static/translations.js")

    assert response.status_code == 200
    assert b'id="language-dialog"' in response.data
    assert b'data-language="vi"' in response.data
    assert b'data-language="en"' in response.data
    assert b'data-language="fr"' in response.data
    assert b'data-language="de"' in response.data
    assert translations.status_code == 200
    assert b"window.safewebTranslations" in translations.data


def test_predict_rejects_empty_or_malformed_payloads() -> None:
    client = create_app(_bundle()).test_client()

    empty = client.post("/predict", json={"url": ""})
    malformed = client.post("/predict", json={"url": "ftp://example.com"})
    not_json = client.post("/predict", data="not-json", content_type="text/plain")

    assert empty.status_code == 400
    assert empty.json["error"]["code"] == "invalid_url"
    assert malformed.status_code == 400
    assert not_json.status_code == 400


def test_predict_returns_structured_assessment() -> None:
    response = create_app(_bundle()).test_client().post(
        "/predict", json={"url": "https://example.test/login"}
    )

    assert response.status_code == 200
    assert {
        "prediction",
        "probability",
        "risk_level",
        "features",
        "explanations",
        "disclaimer",
    } <= response.json.keys()
    assert response.json["prediction"] == "phishing"
    assert response.json["risk_level"] == "HIGH"


def test_predict_reports_missing_model_without_stack_trace() -> None:
    response = create_app(model_path="missing-model.joblib").test_client().post(
        "/predict", json={"url": "https://example.com"}
    )

    assert response.status_code == 503
    assert response.json == {
        "error": {"code": "model_unavailable", "message": "No trained model is available yet."}
    }


def test_predict_cors_allows_only_configured_origin(monkeypatch) -> None:
    monkeypatch.setenv("SAFEWEB_ALLOWED_ORIGIN", "https://jerryishere.github.io")
    client = create_app(_bundle()).test_client()

    allowed = client.options(
        "/predict",
        headers={
            "Origin": "https://jerryishere.github.io",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    rejected = client.post(
        "/predict",
        json={"url": "https://example.test"},
        headers={"Origin": "https://attacker.example"},
    )

    assert allowed.headers["Access-Control-Allow-Origin"] == "https://jerryishere.github.io"
    assert allowed.headers["Access-Control-Allow-Methods"] == "POST, OPTIONS"
    assert "Access-Control-Allow-Origin" not in rejected.headers