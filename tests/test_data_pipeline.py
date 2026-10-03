import pytest

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


@pytest.mark.parametrize(
    ("contents", "message"),
    [
        ("url\nhttps://example.test\n", "required columns"),
        ("url,label\n,0\n", "must not be empty"),
        ("url,label\nexample.com,0\n", "invalid HTTP\\(S\\) URLs"),
        ("url,label\nhttps://example.test,2\n", "either 0"),
        ("url,label\nhttps://example.test,\n", "must not be missing"),
        (
            "url,label\nhttps://example.test,0\nhttps://example.test,1\n",
            "conflicting labels",
        ),
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
    [None, "", "   ", "example.com", "ftp://example.com", "https://bad host.test", "http://[bad"],
)
def test_validate_url_rejects_invalid_input(url) -> None:
    with pytest.raises(ValueError):
        validate_url(url)


@pytest.mark.parametrize("url", ["https://example.com", "http://192.0.2.1/path"])
def test_validate_url_accepts_http_and_https(url) -> None:
    assert validate_url(url) == url