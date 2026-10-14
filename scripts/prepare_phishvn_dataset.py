"""Prepare the open PhishVN archive while preserving its temporal group split."""

from __future__ import annotations

import argparse
from io import BytesIO
import json
from pathlib import Path
import sys
import zipfile
from urllib.parse import urlsplit

import pandas as pd
import tldextract

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.url_validation import normalize_url, validate_url


DEFAULT_SOURCE = PROJECT_ROOT / "PhishVN A Time-Stamped Vietnamese URL Phishing Dat.zip"
RELOCATED_SOURCE = PROJECT_ROOT / "data" / "raw" / DEFAULT_SOURCE.name
if not DEFAULT_SOURCE.is_file() and RELOCATED_SOURCE.is_file():
    DEFAULT_SOURCE = RELOCATED_SOURCE
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "phishvn_clean.csv"
DEFAULT_INDEX = PROJECT_ROOT / "data" / "phishvn_database.json"
INNER_ARCHIVE = "PhishVN A Time-Stamped Vietnamese URL Phishing Dat/PhishVN_v3.1.0_open.zip"
CORE_DATA = "data/dataset_url.csv"
FEATURE_DATA = "data/vn_compphish.csv"
SOURCE_FEATURES = (
    "url_len", "dom_len", "is_ip", "tld_len", "subdom_cnt", "letter_cnt",
    "digit_cnt", "special_cnt", "eq_cnt", "qm_cnt", "amp_cnt", "dot_cnt",
    "dash_cnt", "under_cnt", "letter_ratio", "digit_ratio", "spec_ratio",
    "slash_cnt", "entropy", "path_len", "query_len",
)
_DOMAIN_PARSER = tldextract.TLDExtract(suffix_list_urls=())


def _read_sources(source_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    if source_path.suffix.lower() != ".zip":
        raise ValueError("The authoritative PhishVN source must be its released ZIP archive.")
    with zipfile.ZipFile(source_path) as outer:
        with zipfile.ZipFile(BytesIO(outer.read(INNER_ARCHIVE))) as archive:
            core = pd.read_csv(archive.open(CORE_DATA), low_memory=False)
            features = pd.read_csv(archive.open(FEATURE_DATA), low_memory=False)
    return core, features


def _url_key(
    value: str,
    *,
    strip_www: bool = True,
    lowercase_path: bool = False,
) -> str:
    canonical = normalize_url(value, strip_www=strip_www)
    parts = urlsplit(canonical)
    path = parts.path.rstrip("/")
    query = parts.query
    if lowercase_path:
        path = path.lower()
        query = query.lower()
    return f"{parts.netloc.lower()}{path}?{query}".rstrip("?")


def _analysis_url(value: object, preferred: object = None) -> str:
    if not isinstance(value, str) or not value.strip() or "..." in value:
        return ""
    for candidate_value in (preferred, value):
        if not isinstance(candidate_value, str) or not candidate_value.strip() or "..." in candidate_value:
            continue
        raw = candidate_value.strip()
        candidate = raw if "://" in raw else f"https://{raw}"
        try:
            validate_url(candidate)
            return candidate
        except ValueError:
            continue
    return ""


def prepare_dataset(
    source_path: Path,
    output_path: Path,
    index_output: Path = DEFAULT_INDEX,
) -> dict[str, object]:
    """Canonicalize identities, discard conflicting labels and retain latest rows."""
    frame, feature_frame = _read_sources(source_path)
    required = {"url", "label", "split", "collected_at", "scraped_at", "suspicious_tld"}
    if missing := required - set(frame.columns):
        raise ValueError(f"PhishVN source is missing required fields: {', '.join(sorted(missing))}")
    if not set(SOURCE_FEATURES).issubset(feature_frame.columns):
        raise ValueError("PhishVN companion table is missing CompPhish feature columns.")

    feature_frame = feature_frame.copy()
    feature_frame["_feature_key"] = feature_frame["url"].map(
        lambda value: _url_key(str(value), strip_www=False, lowercase_path=True)
    )
    if feature_frame["_feature_key"].duplicated().any():
        raise ValueError("PhishVN companion feature URLs are not unique by exact host variant.")
    feature_columns = {name: f"phishvn_{name}" for name in SOURCE_FEATURES}
    feature_map = feature_frame.set_index("_feature_key")[list(SOURCE_FEATURES)].rename(columns=feature_columns)

    source_row_count = len(frame)
    prepared = frame.copy()
    preferred_urls = prepared.get("url_norm", pd.Series(None, index=prepared.index))
    prepared["url"] = [
        _analysis_url(raw, preferred)
        for raw, preferred in zip(prepared["url"], preferred_urls, strict=True)
    ]
    prepared = prepared[prepared["url"].ne("")].copy()
    invalid_rows_removed = source_row_count - len(prepared)
    prepared["label"] = prepared["label"].astype(str).str.lower().map(
        {"benign": 0, "legitimate": 0, "phishing": 1, "malicious": 1}
    )
    if prepared["label"].isna().any():
        raise ValueError("PhishVN source contains labels outside benign/phishing.")
    prepared["_feature_key"] = prepared["url"].map(
        lambda value: _url_key(value, strip_www=False, lowercase_path=True)
    )
    prepared["_key"] = prepared["url"].map(_url_key)
    prepared = prepared.join(feature_map, on="_feature_key", validate="many_to_one")
    if prepared[list(feature_columns.values())].isna().any().any():
        raise ValueError("Some PhishVN records do not join to their pre-extracted feature rows.")

    label_counts = prepared.groupby("_key")["label"].nunique()
    conflicts = set(label_counts[label_counts.gt(1)].index)
    conflicting_rows_removed = int(prepared["_key"].isin(conflicts).sum())
    prepared = prepared[~prepared["_key"].isin(conflicts)].copy()
    duplicate_count = int(prepared["_key"].duplicated().sum())
    collected = pd.to_datetime(prepared["collected_at"], format="mixed", dayfirst=True, utc=True, errors="coerce")
    scraped = pd.to_datetime(prepared["scraped_at"], format="mixed", utc=True, errors="coerce")
    tier_rank = prepared.get("tier", pd.Series("", index=prepared.index)).astype(str).str.lower().map(
        {"gold": 3, "silver": 2, "bronze": 1}
    ).fillna(0)
    prepared["_collected_order"] = collected
    prepared["_scraped_order"] = scraped
    prepared["_tier_order"] = tier_rank
    prepared = prepared.sort_values(
        ["_collected_order", "_scraped_order", "_tier_order"],
        ascending=False,
        kind="stable",
    ).drop_duplicates("_key", keep="first")

    split_domains: dict[str, set[str]] = {}
    for split, group in prepared.groupby("split"):
        domains = set()
        for url in group["url"]:
            host = urlsplit(url).hostname or ""
            extracted = _DOMAIN_PARSER(host)
            domains.add(extracted.top_domain_under_public_suffix or host)
        split_domains[str(split)] = domains
    overlaps = {
        f"{left}-{right}": len(split_domains.get(left, set()) & split_domains.get(right, set()))
        for left, right in (("train", "val"), ("train", "test"), ("val", "test"))
    }
    if any(overlaps.values()):
        raise ValueError(f"Upstream PhishVN partitions overlap by registrable domain: {overlaps}")

    prepared["_host"] = prepared["url"].map(lambda value: (urlsplit(value).hostname or "").lower())
    host_labels = prepared.groupby("_host")["label"].nunique()
    phishing_hosts = set(
        prepared.groupby("_host")["label"].first().loc[lambda values: values.eq(1)].index
    ) - set(host_labels[host_labels.gt(1)].index)
    host_profiles = {}
    for host, group in prepared.groupby("_host", sort=True):
        first = group.iloc[0]
        profile = {
            "phishvn_dom_len": int(first["phishvn_dom_len"]),
            "phishvn_tld_len": int(first["phishvn_tld_len"]),
            "phishvn_subdom_cnt": int(first["phishvn_subdom_cnt"]),
            "phishvn_suspicious_tld": int(first["suspicious_tld"]),
        }
        if any(
            group[column].nunique(dropna=False) > 1
            for column in (
                "phishvn_dom_len",
                "phishvn_tld_len",
                "phishvn_subdom_cnt",
                "suspicious_tld",
            )
        ):
            raise ValueError(f"PhishVN host-level features conflict for {host}.")
        host_profiles[host] = [
            profile["phishvn_dom_len"],
            profile["phishvn_tld_len"],
            profile["phishvn_subdom_cnt"],
            profile["phishvn_suspicious_tld"],
        ]

    signatures = prepared[[*feature_columns.values(), "suspicious_tld", "label"]].copy()
    signature_columns = [*feature_columns.values(), "suspicious_tld"]
    signatures["_signature"] = signatures[signature_columns].apply(
        lambda row: ",".join(f"{float(value):.5f}" for value in row), axis=1
    )
    signature_labels = signatures.groupby("_signature")["label"].nunique()
    phishing_signatures = set(
        signatures.groupby("_signature")["label"].first().loc[lambda values: values.eq(1)].index
    ) - set(signature_labels[signature_labels.gt(1)].index)
    url_labels = prepared.groupby("_key")["label"].first()
    known_urls = sorted(url_labels[url_labels.eq(1)].index)
    database = {
        "source": "PhishVN v3.1.0 open URL dataset",
        "knownPhishingUrlKeys": known_urls,
        "knownPhishingHosts": sorted(phishing_hosts),
        "knownPhishingFeatureSignatures": sorted(phishing_signatures),
        "hostProfiles": host_profiles,
        "hostProfileFields": [
            "phishvn_dom_len",
            "phishvn_tld_len",
            "phishvn_subdom_cnt",
            "phishvn_suspicious_tld",
        ],
        "suspiciousTlds": sorted(
            prepared.loc[prepared["suspicious_tld"].astype(float).gt(0), "tld"]
            .dropna().astype(str).str.lower().unique()
        ),
        "signatureFeatureNames": signature_columns,
    }

    columns = [
        "url", "label", "source", "tier", "scenario", "impersonated_org", "domain", "url_norm",
        "tld", "suspicious_tld", "collected_at", "scraped_at", "label_source", "split", "id",
        *feature_columns.values(),
    ]
    columns = [name for name in columns if name in prepared.columns]
    prepared = prepared[columns].sort_values(["split", "url"], kind="stable").reset_index(drop=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prepared.to_csv(output_path, index=False)
    index_output.parent.mkdir(parents=True, exist_ok=True)
    index_output.write_text(json.dumps(database, separators=(",", ":"), ensure_ascii=True), encoding="utf-8")
    return {
        "source_rows": int(source_row_count),
        "rows": int(len(prepared)),
        "phishing": int((prepared["label"] == 1).sum()),
        "benign": int((prepared["label"] == 0).sum()),
        "splits": {str(name): int(count) for name, count in prepared["split"].value_counts().items()},
        "conflicting_urls_removed": len(conflicts),
        "conflicting_rows_removed": conflicting_rows_removed,
        "duplicate_rows_removed": duplicate_count,
        "invalid_or_truncated_rows_removed": int(invalid_rows_removed),
        "registrable_domain_overlaps": overlaps,
        "pre_extracted_feature_columns": len(SOURCE_FEATURES),
        "phishing_url_signatures": len(known_urls),
        "phishing_host_signatures": len(phishing_hosts),
        "exclusive_phishing_feature_signatures": len(phishing_signatures),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--index-output", type=Path, default=DEFAULT_INDEX)
    args = parser.parse_args()
    summary = prepare_dataset(args.source, args.output, args.index_output)
    print(summary)


if __name__ == "__main__":
    main()