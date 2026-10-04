"""Flask interface for URL-string analysis."""

from pathlib import Path
from typing import Any

from flask import Flask, current_app, jsonify, render_template, request

from src.config import risk_thresholds_from_environment
from src.predict import DEFAULT_MODEL_PATH, load_model, predict_url
from src.url_validation import validate_url


def create_app(
    model_bundle: dict[str, Any] | None = None,
    model_path: str | Path = DEFAULT_MODEL_PATH,
) -> Flask:
    """Create the application, optionally using an already-loaded model bundle."""
    app = Flask(__name__)
    if model_bundle is None and Path(model_path).is_file():
        model_bundle = load_model(model_path)
    app.config["MODEL_BUNDLE"] = model_bundle
    app.config["MODEL_PATH"] = Path(model_path)
    app.config["RISK_THRESHOLDS"] = risk_thresholds_from_environment()

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            home_url="/",
            asset_version="dev",
        )

    @app.get("/health")
    def health():
        return jsonify({
            "status": "ok",
            "model_loaded": app.config["MODEL_BUNDLE"] is not None,
        })

    @app.post("/predict")
    def predict():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return _error("invalid_request", "Send a JSON object containing a URL.", 400)
        try:
            url = validate_url(payload.get("url"))
        except ValueError as error:
            return _error("invalid_url", str(error), 400)

        try:
            result = predict_url(
                url,
                bundle=current_app.config["MODEL_BUNDLE"],
                thresholds=current_app.config["RISK_THRESHOLDS"],
                model_path=current_app.config["MODEL_PATH"],
            )
        except Exception:
            current_app.logger.exception("SafeWeb prediction failed")
            return _error("prediction_unavailable", "The model could not assess this URL.", 503)
        if result["status"] == "model_not_loaded":
            return _error("model_unavailable", "No trained model is available yet.", 503)
        return jsonify(result)

    return app


def _error(code: str, message: str, status: int):
    return jsonify({"error": {"code": code, "message": message}}), status


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)