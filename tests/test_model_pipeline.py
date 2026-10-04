import json

from src.evaluate import evaluate_model
from src.predict import load_model, predict_url
from src.train import train_model
from web.app import create_app


def _dataset_csv(path) -> None:
    rows = [
        ("https://legit-one.example/about", 0),
        ("https://legit-two.example/home", 0),
        ("https://legit-three.example/contact", 0),
        ("https://legit-four.example/news", 0),
        ("https://legit-five.example/products", 0),
        ("http://verify-one.example/login", 1),
        ("http://verify-two.example/account", 1),
        ("http://verify-three.example/password", 1),
        ("http://verify-four.example/payment", 1),
        ("http://verify-five.example/confirm", 1),
    ]
    path.write_text("url,label\n" + "".join(f"{url},{label}\n" for url, label in rows), encoding="utf-8")


def test_train_predict_and_evaluate_generate_artifacts(tmp_path) -> None:
    dataset_path = tmp_path / "temporary_test_data.csv"
    model_path = tmp_path / "random_forest.joblib"
    report_path = tmp_path / "reports"
    _dataset_csv(dataset_path)

    summary = train_model(dataset_path, model_path)
    bundle = load_model(model_path)
    prediction = predict_url("https://sample.example/login", bundle)
    metrics = evaluate_model(dataset_path, model_path, report_path)

    assert summary == {
        "rows": 10,
        "training_rows": 8,
        "testing_rows": 2,
        "legitimate": 5,
        "phishing": 5,
    }
    assert bundle["model"].n_estimators == 200
    assert bundle["model"].random_state == 42
    assert bundle["feature_names"]
    assert prediction["prediction"] in {"legitimate", "phishing"}
    assert 0.0 <= prediction["probability"] <= 1.0
    assert prediction["risk_level"] in {"LOW", "MEDIUM", "HIGH"}
    assert {"accuracy", "precision", "recall", "f1_score", "confusion_matrix"} <= metrics.keys()
    assert json.loads((report_path / "metrics.json").read_text(encoding="utf-8"))["test_rows"] == 2
    assert (report_path / "classification_report.txt").exists()
    assert (report_path / "confusion_matrix.png").exists()
    assert (report_path / "feature_importance.png").exists()
    assert (report_path / "error_analysis.csv").exists()

    client = create_app(model_path=model_path).test_client()
    assert b"MODEL READY" in client.get("/").data
    assert client.post("/predict", json={"url": "https://sample.example/login"}).status_code == 200