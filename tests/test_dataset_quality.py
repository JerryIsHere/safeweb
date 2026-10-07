from pathlib import Path

from src.data_quality import (
    analyze_dataset,
    domain_disjoint_split,
    is_punycode_or_idn,
    normalize_url_for_similarity,
)


def test_dataset_quality_reports_requested_distributions() -> None:
    summary = analyze_dataset("data/raw/urls.csv")

    assert summary["rows"] == 718
    assert summary["class_balance"] == {"legitimate": 218, "phishing": 500}
    assert summary["exact_duplicates"] == 0
    assert summary["near_duplicates"] == 126
    assert summary["overlapping_domains"] == 11
    assert summary["overlapping_hostname_families"] == 5
    assert summary["short_phishing_urls"] == 147
    assert summary["long_legitimate_urls"] == 0
    assert summary["https_urls"] == 376
    assert summary["ip_hosts"] == 0
    assert summary["punycode_or_idn"] == 0
    assert summary["percent_encoded_urls"] == 0
    assert summary["suspicious_keyword_urls"] == 497


def test_domain_disjoint_split_removes_overlapping_domains() -> None:
    dataset = Path("data/raw/urls.csv")
    train, test = domain_disjoint_split(dataset, test_size=0.20)

    train_domains = {normalize_url_for_similarity(url)[1] for url in train["url"]}
    test_domains = {normalize_url_for_similarity(url)[1] for url in test["url"]}
    assert train_domains.isdisjoint(test_domains)
    assert set(train["label"]).issubset({0, 1})
    assert set(test["label"]).issubset({0, 1})


def test_punycode_and_idn_detection() -> None:
    assert is_punycode_or_idn("https://xn--bcher-kva.example/") == 1
    assert is_punycode_or_idn("https://пример.рф/") == 1
    assert is_punycode_or_idn("https://example.com/") == 0
