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
    bundle = load_model(DEFAULT_MODEL_PATH)
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
        python_result = predict_url(url, bundle=bundle)
        if not browser_result["ok"]:
            raise AssertionError(f"Browser rejected valid URL {url!r}: {browser_result}")
        result = browser_result["result"]
        if result["prediction"] != python_result["prediction"]:
            raise AssertionError(f"Prediction mismatch for {url!r}.")
        if result["risk_level"] != python_result["risk_level"]:
            raise AssertionError(f"Risk level mismatch for {url!r}.")
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
        probability_delta = abs(result["probability"] - python_result["probability"])
        max_probability_delta = max(max_probability_delta, probability_delta)
        if probability_delta > 1e-12:
            raise AssertionError(
                f"Probability differs for {url!r}: {result['probability']} != "
                f"{python_result['probability']}."
            )

    for url, browser_result in zip(INVALID_URLS, browser_results[len(VALID_URLS):], strict=True):
        try:
            validate_url(url)
            python_valid = True
        except ValueError:
            python_valid = False
        if browser_result["ok"] != python_valid:
            raise AssertionError(f"Validation mismatch for {url!r}.")

    print(
        f"Parity passed for {len(VALID_URLS)} valid and {len(INVALID_URLS)} invalid URLs; "
        f"max feature delta={max_feature_delta:.3g}, "
        f"max probability delta={max_probability_delta:.3g}."
    )


if __name__ == "__main__":
    main()