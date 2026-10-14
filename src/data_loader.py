"""Load and validate URL classification datasets."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

import pandas as pd

from src.url_validation import normalize_url, validate_url


REQUIRED_COLUMNS = {"url", "label"}
_LABEL_MAP = {
    "0": 0,
    "1": 1,
    "legitimate": 0,
    "benign": 0,
    "safe": 0,
    "phishing": 1,
    "malicious": 1,
    "fraud": 1,
}


def _normalize_url(raw_value: object, preferred_value: object | None = None) -> str:
    """Return a canonical HTTP(S) URL while accepting project dataset variants."""
    candidates = [preferred_value, raw_value]
    first_invalid = ""
    for candidate in candidates:
        if candidate is None or pd.isna(candidate):
            continue
        value = str(candidate).strip()
        if not value:
            continue
        try:
            return normalize_url(value, strip_www=True)
        except ValueError:
            if not first_invalid:
                first_invalid = value
            continue
    return first_invalid


def _coerce_labels(label_series: pd.Series) -> pd.Series:
    """Map common label spellings to 0/1 integers."""
    normalized = label_series.astype(str).str.strip().str.lower()
    mapped = normalized.map(_LABEL_MAP.get)
    if mapped.isna().any():
        raise ValueError("Dataset labels must be either 0 (legitimate) or 1 (phishing).")
    return mapped.astype(int)


def _dedup_url_key(url: str) -> str:
    parts = urlsplit(url)
    hostname = (parts.hostname or "").lower().rstrip(".")
    if hostname.startswith("www."):
        hostname = hostname[4:]
    port = parts.port
    if port is not None and not (parts.scheme == "http" and port == 80) and not (
        parts.scheme == "https" and port == 443
    ):
        hostname += f":{port}"
    path = parts.path.rstrip("/").lower()
    query = parts.query.lower()
    return f"{hostname}{path}?{query}".rstrip("?")


def class_distribution(frame: pd.DataFrame) -> dict[str, int]:
    """Return labeled row counts for the two project classes."""
    counts = frame["label"].value_counts()
    return {"legitimate": int(counts.get(0, 0)), "phishing": int(counts.get(1, 0))}


def load_dataset(path: str | Path) -> pd.DataFrame:
    """Load a CSV containing non-empty URLs and binary labels.

    Exact duplicate URLs are removed, keeping their first occurrence.
    """
    try:
        frame = pd.read_csv(path)
    except FileNotFoundError as error:
        raise ValueError(f"Dataset file not found: {path}") from error
    except pd.errors.EmptyDataError as error:
        raise ValueError(f"Dataset file is empty or has no CSV header: {path}") from error
    except pd.errors.ParserError as error:
        raise ValueError(f"Dataset CSV is malformed: {path}") from error
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {', '.join(sorted(missing))}")

    frame = frame.copy()
    preferred_urls = None
    if "url_norm" in frame.columns:
        preferred_urls = frame["url_norm"].where(frame["url_norm"].notna(), None)

    frame["url"] = frame.apply(
        lambda row: _normalize_url(row.get("url"), preferred_urls.iloc[row.name] if preferred_urls is not None else None),
        axis=1,
    )
    if frame["label"].isna().any():
        raise ValueError("Dataset labels must not be missing.")
    frame["label"] = _coerce_labels(frame["label"])

    if frame["url"].isna().any() or frame["url"].eq("").any():
        raise ValueError("Dataset URLs must not be empty.")
    invalid_url_rows = []
    for row_number, url in enumerate(frame["url"], start=2):
        try:
            validate_url(url)
        except ValueError:
            invalid_url_rows.append(row_number)
    if invalid_url_rows:
        rows = ", ".join(map(str, invalid_url_rows[:10]))
        suffix = " ..." if len(invalid_url_rows) > 10 else ""
        raise ValueError(f"Dataset contains invalid HTTP(S) URLs at CSV row(s): {rows}{suffix}.")
    frame["_identity"] = frame["url"].map(_dedup_url_key)
    duplicate_labels = frame.groupby("_identity")["label"].nunique(dropna=False)
    conflicting_urls = set(duplicate_labels[duplicate_labels.gt(1)].index)
    frame = frame[~frame["_identity"].isin(conflicting_urls)].copy()
    sort_columns = []
    for column in ("collected_at", "scraped_at"):
        if column in frame:
            frame[f"_{column}_order"] = pd.to_datetime(
                frame[column], format="mixed", dayfirst=True, utc=True, errors="coerce"
            )
            sort_columns.append(f"_{column}_order")
    if sort_columns:
        frame = frame.sort_values(sort_columns, ascending=False, kind="stable")
    frame = frame[["url", "label", "_identity"]].drop_duplicates(subset="_identity", keep="first")
    frame = frame[["url", "label"]].reset_index(drop=True)
    if frame.empty:
        raise ValueError("Dataset must contain at least one valid data row.")
    return frame