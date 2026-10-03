import pytest

from src.feature_extractor import extract_features


def test_extracts_features_for_https_url() -> None:
    features = extract_features("https://www.example.com/login?next=home")

    assert features["has_https"] == 1
    assert features["domain_length"] == len("www.example.com")
    assert features["num_subdomains"] == 1
    assert features["has_query"] == 1
    assert features["keyword_login"] == 1
    assert features["url_entropy"] > 0


def test_http_url_is_not_marked_as_https() -> None:
    features = extract_features("http://example.com/path")

    assert features["has_https"] == 0
    assert features["path_length"] == len("/path")


def test_detects_ipv4_and_ipv6_hosts() -> None:
    assert extract_features("http://192.0.2.10/path")["has_ip"] == 1
    assert extract_features("http://[2001:db8::1]/path")["has_ip"] == 1


def test_detects_at_sign_and_url_signals() -> None:
    features = extract_features("http://user@example.com/a//b?x=100%25")

    assert features["has_at"] == 1
    assert features["has_double_slash"] == 1
    assert features["has_percent"] == 1
    assert features["has_equals"] == 1


def test_malformed_url_still_returns_consistent_numeric_features() -> None:
    malformed = extract_features("http://[broken/login")
    normal = extract_features("https://example.com")

    assert malformed.keys() == normal.keys()
    assert all(isinstance(value, (int, float)) for value in malformed.values())


def test_empty_url_is_rejected() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        extract_features("  ")


def test_feature_names_and_values_are_deterministic() -> None:
    url = "http://verify.example.co.uk/reset?id=1"

    assert extract_features(url) == extract_features(url)
    assert extract_features(url)["num_subdomains"] == 1


def test_counts_multiple_hostname_subdomains() -> None:
    assert extract_features("https://one.two.example.co.uk/")["num_subdomains"] == 2


def test_keyword_detection_is_case_insensitive() -> None:
    assert extract_features("https://example.com/LoGiN")["keyword_login"] == 1


def test_entropy_of_repeated_characters_is_zero() -> None:
    assert extract_features("aaaa")["url_entropy"] == 0