"""Prepare the documented PhishVN training dataset for SafeWeb.

The upstream source retains a richer metadata schema than the project's training
loader. This script picks the normalized URL, maps the source labels to the
binary classes required by the model, preserves audit metadata, and writes a
reproducible training CSV without modifying the original raw source file.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_ROOT / "data" / "raw" / "urls_completed.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "raw" / "PhishVN_training_5000.csv"


def normalize_dataset(source_path: Path, output_path: Path) -> dict[str, int | str]:
    """Create a SafeWeb-compatible training file from the PhishVN CSV."""
    frame = pd.read_csv(source_path)
    if set({"url", "label"}) - set(frame.columns):
        raise ValueError("Source dataset must contain url and label columns.")

    prepared = frame.copy()
    prepared["url"] = prepared["url_norm"].fillna(prepared["url"]).astype(str).str.strip()
    prepared["label"] = prepared["label"].map({"benign": 0, "legitimate": 0, "phishing": 1, "malicious": 1}).astype(int)
    prepared = prepared[[
        "url",
        "label",
        "source",
        "tier",
        "scenario",
        "impersonated_org",
        "domain",
        "url_norm",
        "collected_at",
        "label_source",
        "split",
        "id",
    ]].copy()

    duplicate_normalized = prepared["url"].duplicated(keep="first")
    if duplicate_normalized.any():
        duplicates = int(duplicate_normalized.sum())
        prepared = prepared.loc[~duplicate_normalized].reset_index(drop=True)
    else:
        duplicates = 0

    conflicting = prepared.groupby("url")["label"].nunique(dropna=False)
    if (conflicting > 1).any():
        raise ValueError("Normalized duplicate URLs have conflicting labels.")

    tier_counts = prepared["tier"].value_counts(dropna=False).to_dict()
    summary = {
        "rows": int(len(prepared)),
        "phishing": int((prepared["label"] == 1).sum()),
        "benign": int((prepared["label"] == 0).sum()),
        "tier_counts": tier_counts,
        "duplicates_removed": int(duplicates),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    prepared.to_csv(output_path, index=False)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    summary = normalize_dataset(arguments.source, arguments.output)
    print(
        "Prepared dataset: "
        f"rows={summary['rows']}, benign={summary['benign']}, phishing={summary['phishing']}, "
        f"removed_duplicates={summary['duplicates_removed']}, tier_counts={summary['tier_counts']}"
    )


if __name__ == "__main__":
    main()
