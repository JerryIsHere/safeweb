"""Load and validate URL classification datasets."""

from pathlib import Path

import pandas as pd

from src.url_validation import validate_url


REQUIRED_COLUMNS = {"url", "label"}


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
    frame = frame.loc[:, ["url", "label"]].copy()
    if frame["url"].isna().any():
        raise ValueError("Dataset URLs must not be empty.")
    if frame["label"].isna().any():
        raise ValueError("Dataset labels must not be missing.")
    frame["url"] = frame["url"].astype(str).str.strip()
    if frame["url"].eq("").any():
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
    duplicate_labels = frame.groupby("url")["label"].nunique(dropna=False)
    if duplicate_labels.gt(1).any():
        raise ValueError("Duplicate URLs must not have conflicting labels.")
    labels = pd.to_numeric(frame["label"], errors="coerce")
    if labels.isna().any() or not labels.isin([0, 1]).all():
        raise ValueError("Dataset labels must be either 0 (legitimate) or 1 (phishing).")
    frame["label"] = labels.astype(int)
    frame = frame.drop_duplicates(subset="url", keep="first").reset_index(drop=True)
    if frame.empty:
        raise ValueError("Dataset must contain at least one valid data row.")
    return frame