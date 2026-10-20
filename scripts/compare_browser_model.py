"""Compare browser inference with the current Python model on fixed URL cases."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.predict import DEFAULT_MODEL_PATH, load_model, predict_url
from src.url_validation import validate_url


PARITY_REPORT_PATH = PROJECT_ROOT / "reports" / "browser_model_parity.json"
VALID_URLS = (
    "https://www.example.com/login?next=home",
    "http://one.two.example.co.uk/account/reset?id=123",
    "https://example.com/a//b?token=abc%2Fdef&x=1",
    "http://192.0.2.10/path?x=1",
    "https://[2001:db8::1]/signin",
    "https://example.com/" + "a" * 120 + "?ref=verify",
    "https://пример.рф/подтвердить?x=1",
    "https://example.com/a#fragment?ignored",
    "https://a.b.ck/",
    "https://x.www.ck/",
)
INVALID_URLS = (
    "",
    "   ",
    "ftp://example.com",
    "https://bad host.test",
    "http://[bad",
    "http://example.com:99999",
)

NODE_COMPARISON = r"""
const fs = require("node:fs");
require("./web/static/model-data.js");
const browser = require("./web/static/browser-model.js");
const urls = JSON.parse(fs.readFileSync(0, "utf8"));
const results = urls.map((url) => {
  try { return { ok: true, result: browser.assessUrl(url) }; }
  catch (error) { return { ok: false, error: error.message }; }
});
process.stdout.write(JSON.stringify(results));
"""


def main() -> None:
    model_names = ("random_forest", "gradient_boosting", "svm", "logistic_regression")
    bundles = {
        name: load_model(DEFAULT_MODEL_PATH.with_name(f"{name}.joblib"))
        for name in model_names
    }
    bundle = bundles["random_forest"]
    urls = [*VALID_URLS, *INVALID_URLS]
    completed = subprocess.run(
        ["node", "-e", NODE_COMPARISON],
        input=json.dumps(urls, ensure_ascii=False),
        capture_output=True,
        check=True,
        cwd=PROJECT_ROOT,
        text=True,
    )
    browser_results = json.loads(completed.stdout)
    max_feature_delta = 0.0
    max_probability_delta = 0.0

    for url, browser_result in zip(
        VALID_URLS, browser_results[:len(VALID_URLS)], strict=True
    ):
        python_results = {
            name: predict_url(url, bundle=model_bundle)
            for name, model_bundle in bundles.items()
        }
        python_result = python_results["random_forest"]
        if not browser_result["ok"]:
            raise AssertionError(f"Browser rejected valid URL {url!r}: {browser_result}")
        result = browser_result["result"]
        if result["explanations"] != python_result["explanations"]:
            raise AssertionError(f"Explanation mismatch for {url!r}.")
        if result["features"].keys() != python_result["features"].keys():
            raise AssertionError(f"Feature order mismatch for {url!r}.")
        for name, expected in python_result["features"].items():
            actual = result["features"][name]
            delta = abs(float(actual) - float(expected))
            max_feature_delta = max(max_feature_delta, delta)
            if delta > 1e-12:
                raise AssertionError(f"Feature {name!r} differs for {url!r}: {actual} != {expected}.")
        expected_models = {}
        for name, model_result in python_results.items():
            expected_models[name] = model_result["probability"]
            delta = abs(result["models"][name]["probability"] - model_result["probability"])
            max_probability_delta = max(max_probability_delta, delta)
            if delta > 1e-10:
                raise AssertionError(
                    f"{name} probability differs for {url!r}: "
                    f"{result['models'][name]['probability']} != {model_result['probability']}."
                )
            if result["models"][name]["prediction"] != model_result["prediction"]:
                raise AssertionError(f"{name} prediction mismatch for {url!r}.")
        ensemble_probability = sum(expected_models.values()) / len(expected_models)
        if abs(result["probability"] - ensemble_probability) > 1e-10:
            raise AssertionError(f"Ensemble probability mismatch for {url!r}.")
        if result["prediction"] != ("phishing" if ensemble_probability > 0.5 else "legitimate"):
            raise AssertionError(f"Ensemble prediction mismatch for {url!r}.")

    for url, browser_result in zip(INVALID_URLS, browser_results[len(VALID_URLS):], strict=True):
        try:
            validate_url(url)
            python_valid = True
        except ValueError:
            python_valid = False
        if browser_result["ok"] != python_valid:
            raise AssertionError(f"Validation mismatch for {url!r}.")

    result = {
        "valid_url_cases": len(VALID_URLS),
        "invalid_url_cases": len(INVALID_URLS),
        "max_feature_delta": max_feature_delta,
        "max_probability_delta": max_probability_delta,
        "feature_tolerance": 1e-12,
        "probability_tolerance": 1e-10,
    }
    PARITY_REPORT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        f"Parity passed for {len(VALID_URLS)} valid and {len(INVALID_URLS)} invalid URLs; "
        f"max feature delta={max_feature_delta:.3g}, "
        f"max probability delta={max_probability_delta:.3g}."
    )


if __name__ == "__main__":
    main()