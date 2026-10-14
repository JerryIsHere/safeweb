import json

import pandas as pd
import pytest

from scripts.prepare_phishvn_dataset import DEFAULT_SOURCE, prepare_dataset
from src.data_loader import load_dataset
from src.url_validation import validate_url


def test_load_dataset_validates_and_removes_exact_duplicates(tmp_path) -> None:
    dataset_path = tmp_path / "data.csv"
    dataset_path.write_text(
        "url,label\nhttps://one.example,0\nhttps://two.example,1\nhttps://one.example,0\n",
        encoding="utf-8",
    )

    dataset = load_dataset(dataset_path)

    assert list(dataset.columns) == ["url", "label"]
    assert len(dataset) == 2
    assert set(dataset["label"]) == {0, 1}


def test_load_dataset_accepts_phishvn_style_labels_and_normalized_urls(tmp_path) -> None:
    dataset_path = tmp_path / "phishvn.csv"
    dataset_path.write_text(
        "url,label,url_norm,source,tier\n"
        "www.example.com,benign,http://www.example.com,feed,gold\n"
        "https://phish.example,phishing,https://phish.example,feed,silver\n"
        "www.example.com,benign,http://www.example.com,feed,gold\n",
        encoding="utf-8",
    )

    dataset = load_dataset(dataset_path)

    assert list(dataset.columns) == ["url", "label"]
    assert dataset["url"].tolist() == ["http://example.com", "https://phish.example"]
    assert dataset["label"].tolist() == [0, 1]


@pytest.mark.parametrize(
    ("contents", "message"),
    [
        ("url\nhttps://example.test\n", "required columns"),
        ("url,label\n,0\n", "must not be empty"),
        ("url,label\nhttps://bad host.test,0\n", "invalid HTTP\\(S\\) URLs"),
        ("url,label\nhttps://example.test,2\n", "either 0"),
        ("url,label\nhttps://example.test,\n", "must not be missing"),
    ],
)
def test_load_dataset_rejects_invalid_rows(tmp_path, contents, message) -> None:
    dataset_path = tmp_path / "invalid.csv"
    dataset_path.write_text(contents, encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_dataset(dataset_path)


@pytest.mark.parametrize(
    ("contents", "message"),
    [(None, "not found"), ("", "empty or has no CSV header")],
)
def test_load_dataset_reports_missing_or_empty_files(tmp_path, contents, message) -> None:
    dataset_path = tmp_path / "dataset.csv"
    if contents is not None:
        dataset_path.write_text(contents, encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_dataset(dataset_path)


@pytest.mark.parametrize(
    "url",
    [None, "", "   ", "ftp://example.com", "https://bad host.test", "http://[bad"],
)
def test_validate_url_rejects_invalid_input(url) -> None:
    with pytest.raises(ValueError):
        validate_url(url)


@pytest.mark.parametrize("url", ["https://example.com", "http://192.0.2.1/path"])
def test_validate_url_accepts_http_and_https(url) -> None:
    assert validate_url(url) == url


@pytest.mark.parametrize(
    ("entered", "expected"),
    [
        ("divineskins.gg", "https://divineskins.gg"),
        ("vietcombank", "https://vietcombank.com"),
        ("vietcombank/login?next=home", "https://vietcombank.com/login?next=home"),
        ("HTTP://WWW.Example.COM:80/path/", "http://www.example.com/path"),
    ],
)
def test_validate_url_heals_and_normalizes_input(entered, expected) -> None:
    assert validate_url(entered) == expected


def test_load_dataset_discards_urls_with_conflicting_labels(tmp_path) -> None:
    dataset_path = tmp_path / "conflicts.csv"
    dataset_path.write_text(
        "url,label\nhttps://conflict.example,0\nhttps://conflict.example,1\nhttps://kept.example,0\n",
        encoding="utf-8",
    )

    dataset = load_dataset(dataset_path)

    assert dataset["url"].tolist() == ["https://kept.example"]


def test_load_dataset_deduplicates_protocol_aliases_and_keeps_latest_timestamp(tmp_path) -> None:
    dataset_path = tmp_path / "timestamped.csv"
    dataset_path.write_text(
        "url,label,collected_at,scraped_at\n"
        "http://www.example.test/path/,0,2025-01-01,2026-01-01T00:00:00Z\n"
        "https://example.test/path,0,2025-02-01,2026-02-01T00:00:00Z\n",
        encoding="utf-8",
    )

    dataset = load_dataset(dataset_path)

    assert len(dataset) == 1
    assert dataset.iloc[0]["url"] == "https://example.test/path"


def test_prepare_phishvn_archive_uses_official_splits_and_precomputed_features(tmp_path) -> None:
    output_path = tmp_path / "clean.csv"
    database_path = tmp_path / "database.json"

    summary = prepare_dataset(DEFAULT_SOURCE, output_path, database_path)
    prepared = pd.read_csv(output_path)
    database = json.loads(database_path.read_text(encoding="utf-8"))

    assert summary["source_rows"] == 53116
    assert summary["rows"] == 36261
    assert summary["duplicate_rows_removed"] == 16855
    assert summary["pre_extracted_feature_columns"] == 21
    assert summary["registrable_domain_overlaps"] == {
        "train-val": 0,
        "train-test": 0,
        "val-test": 0,
    }
    assert set(prepared["split"]) == {"train", "val", "test"}
    assert all(name in prepared for name in ("phishvn_url_len", "phishvn_entropy", "collected_at", "scraped_at"))
    assert database["knownPhishingUrlKeys"]
    assert database["knownPhishingHosts"]
    assert database["knownPhishingFeatureSignatures"]