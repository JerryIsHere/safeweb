from pathlib import Path

import pandas as pd

from src.data_quality import domain_disjoint_split
from src.experimental import train_experimental_model, evaluate_model_pair, evaluate_hard_cases
from src.feature_extractor import EXPERIMENTAL_FEATURE_ORDER


def test_experimental_feature_order_is_stable() -> None:
    features = pd.DataFrame([
        {name: 1 for name in EXPERIMENTAL_FEATURE_ORDER}
    ])
    assert list(features.columns) == list(EXPERIMENTAL_FEATURE_ORDER)


def test_domain_disjoint_split_has_no_overlapping_domains() -> None:
    train, test = domain_disjoint_split("data/raw/urls.csv", test_size=0.20)
    train_domains = {url.split("//", 1)[1].split("/", 1)[0].lower() for url in train["url"]}
    test_domains = {url.split("//", 1)[1].split("/", 1)[0].lower() for url in test["url"]}
    assert train_domains.isdisjoint(test_domains)


def test_experimental_training_and_evaluation_work() -> None:
    model_path = Path("/tmp/safeweb-experimental-test.joblib")
    train = train_experimental_model("data/raw/urls.csv", model_path, feature_mode="experimental")
    scores = evaluate_model_pair("data/raw/urls.csv", experimental_model_path=model_path)
    assert train["feature_count"] > 30
    assert set(scores.keys()) == {"random_split_benchmark", "domain_disjoint_benchmark"}
    assert set(scores["random_split_benchmark"].keys()) == {"baseline", "experimental"}


def test_hard_case_evaluation_runs() -> None:
    path = Path("/tmp/safeweb-hard-case-suite.csv")
    path.write_text(
        "url,label,case_category,source\n"
        "https://example.com/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa?ref=verify,0,long_legitimate,clearly synthetic\n"
        "https://short.example/login,1,short_phishing,clearly synthetic\n",
        encoding="utf-8",
    )
    results = evaluate_hard_cases(path, baseline_model_path="model/random_forest.joblib", experimental_model_path="/tmp/safeweb-experimental-test.joblib")
    assert set(results.keys()) == {"baseline", "experimental"}
