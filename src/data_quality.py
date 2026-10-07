"""Dataset-quality audit utilities for SafeWeb experiments."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from random import Random
from typing import NamedTuple
from urllib.parse import urlsplit

import pandas as pd
import tldextract
from sklearn.model_selection import train_test_split

from src.data_loader import load_dataset


_DOMAIN_PARSER = tldextract.TLDExtract(suffix_list_urls=())


class SplitResult(NamedTuple):
    """A train/test split returned by the domain-disjoint assignment."""

    train: pd.DataFrame
    test: pd.DataFrame


def normalize_url_for_similarity(url: str) -> tuple[str, str]:
    """Return a canonical host/path representation and the hostname."""
    parsed = urlsplit(url.strip())
    hostname = (parsed.hostname or "").lower().rstrip(".")
    normalized_path = parsed.path.rstrip("/") or "/"
    normalized = f"{hostname}{normalized_path}?{parsed.query}".lower()
    return normalized, hostname


def _hostname_family(hostname: str) -> str:
    """Return a hostname family used for domain-disjoint grouping."""
    if not hostname:
        return ""
    extracted = _DOMAIN_PARSER(hostname)
    registrable = extracted.registered_domain or hostname
    if "." not in registrable:
        return registrable
    labels = registrable.split(".")
    return ".".join(labels[:2]) if len(labels) > 1 else labels[0]


def _near_duplicate_count(frame: pd.DataFrame) -> int:
    normalized = frame["url"].map(normalize_url_for_similarity)
    return int(pd.Series(normalized).map(lambda item: item[0]).duplicated().sum())


def analyze_dataset(path: str | Path) -> dict[str, object]:
    """Report dataset quality and leakage indicators for a SafeWeb CSV."""
    frame = load_dataset(path)
    lowercase_urls = frame["url"].str.lower()
    hostname_values = lowercase_urls.map(lambda value: urlsplit(value).hostname or "")
    normalized = lowercase_urls.map(normalize_url_for_similarity)
    normalized_hosts = normalized.map(lambda item: item[1])

    class_balance = {
        "legitimate": int((frame["label"] == 0).sum()),
        "phishing": int((frame["label"] == 1).sum()),
    }
    suspicious_keywords = (
        "login",
        "signin",
        "verify",
        "account",
        "password",
        "bank",
        "payment",
        "confirm",
    )
    keyword_pattern = "|".join(re.escape(keyword) for keyword in suspicious_keywords)
    random_train, random_test = train_test_split(
        frame,
        test_size=0.20,
        random_state=42,
        stratify=frame["label"],
    )

    rows = {
        "rows": int(len(frame)),
        "class_balance": class_balance,
        "exact_duplicates": int(frame["url"].duplicated().sum()),
        "near_duplicates": _near_duplicate_count(frame),
        "overlapping_domains": len(
            set(
                random_train["url"]
                .map(lambda value: (urlsplit(value).hostname or "").lower())
                .loc[lambda values: values != ""]
            )
            & set(
                random_test["url"]
                .map(lambda value: (urlsplit(value).hostname or "").lower())
                .loc[lambda values: values != ""]
            )
        ),
        "overlapping_hostname_families": len(
            set(
                random_train["url"]
                .map(lambda value: _hostname_family((urlsplit(value).hostname or "").lower()))
                .loc[lambda values: values != ""]
            )
            & set(
                random_test["url"]
                .map(lambda value: _hostname_family((urlsplit(value).hostname or "").lower()))
                .loc[lambda values: values != ""]
            )
        ),
        "unique_domains": int(normalized_hosts.nunique()),
        "unique_hostname_families": int(hostname_values.map(_hostname_family).nunique()),
        "url_length_distribution": {
            "minimum": int(frame["url"].str.len().min()),
            "median": float(frame["url"].str.len().median()),
            "maximum": int(frame["url"].str.len().max()),
        },
        "https_urls": int(lowercase_urls.str.startswith("https://").sum()),
        "ip_hosts": int(hostname_values.map(lambda value: bool(value) and _is_ip(value)).sum()),
        "punycode_or_idn": int(
            hostname_values.map(lambda value: is_punycode_or_idn(f"https://{value}/")).sum()
        ),
        "percent_encoded_urls": int(lowercase_urls.str.contains("%", regex=False).sum()),
        "suspicious_keyword_urls": int(
            lowercase_urls.str.contains(keyword_pattern, case=False, regex=True).sum()
        ),
        "short_phishing_urls": int(
            ((frame["label"] == 1) & (frame["url"].str.len() <= 50)).sum()
        ),
        "long_legitimate_urls": int(
            ((frame["label"] == 0) & (frame["url"].str.len() >= 100)).sum()
        ),
        "short_url_threshold": 50,
        "long_url_threshold": 100,
    }
    return rows


def domain_overlap(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    grouping: str = "domain",
) -> int:
    """Return the count of shared domains or hostname families across two splits."""
    if grouping not in {"domain", "hostname_family"}:
        raise ValueError("grouping must be 'domain' or 'hostname_family'.")

    left_set = left["url"].map(lambda value: (urlsplit(value).hostname or "").lower())
    right_set = right["url"].map(lambda value: (urlsplit(value).hostname or "").lower())
    if grouping == "hostname_family":
        left_set = left_set.map(_hostname_family)
        right_set = right_set.map(_hostname_family)
    return int(set(left_set) & set(right_set))


def _is_ip(hostname: str) -> bool:
    try:
        import ipaddress

        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        return False


def is_punycode_or_idn(url: str) -> int:
    """Return 1 when a URL contains punycode or Unicode IDN content."""
    hostname = urlsplit(url).hostname or ""
    if not hostname:
        return 0
    try:
        ascii_hostname = hostname.encode("idna").decode("ascii")
    except UnicodeError:
        return 0
    return int(hostname != ascii_hostname or hostname.startswith("xn--") or "xn--" in hostname)


def domain_disjoint_split(
    dataset: str | Path,
    test_size: float = 0.20,
    random_state: int = 42,
) -> SplitResult:
    """Split a dataset by hostname family so test domains never appear in train."""
    frame = load_dataset(dataset)
    if not 0.0 < test_size < 1.0:
        raise ValueError("test_size must be between 0 and 1.")

    frame = frame.copy()
    frame["hostname"] = frame["url"].map(lambda value: (urlsplit(value).hostname or "").lower())
    frame["family"] = frame["hostname"].map(_hostname_family)
    frame["family"] = frame["family"].replace("", "__unknown__")

    families = frame.groupby("family", group_keys=False)
    randomized = Random(random_state)
    family_rows = list(families)
    randomized.shuffle(family_rows)

    target_rows = max(1, int(round(len(frame) * test_size)))
    test_rows: list[pd.DataFrame] = []
    test_count = 0
    selected_families: set[str] = set()

    for _, family_frame in family_rows:
        if test_count >= target_rows:
            break
        test_rows.append(family_frame)
        test_count += len(family_frame)
        selected_families.add(family_frame["family"].iloc[0])

    test = pd.concat(test_rows, ignore_index=True) if test_rows else frame.iloc[:0].copy()
    test = test.drop(columns=["family", "hostname"])
    train = frame.loc[~frame["family"].isin(selected_families)].drop(columns=["family", "hostname"])

    if train.empty or test.empty:
        raise ValueError("Unable to create a domain-disjoint split with the current dataset.")

    if train["label"].nunique() < 2 or test["label"].nunique() < 2:
        raise ValueError("Domain-disjoint evaluation requires both labels in each split.")

    return SplitResult(train=train.reset_index(drop=True), test=test.reset_index(drop=True))


def build_hard_case_suite(path: str | Path) -> pd.DataFrame:
    """Return a documented, clearly synthetic hard-case evaluation suite."""
    rows = [
        ("https://example.com/" + ("a" * 120) + "?ref=verify", 0, "long_legitimate", "clearly synthetic"),
        ("https://short.example/login", 1, "short_phishing", "clearly synthetic"),
        ("https://secure-login.example/verify?continue=account", 1, "https_phishing", "clearly synthetic"),
        ("https://example.com/account", 0, "legitimate_with_suspicious_keyword", "clearly synthetic"),
        ("https://update-profile.example/auth/validate", 1, "phishing_without_keyword", "clearly synthetic"),
        ("http://192.0.2.10/path?x=1", 1, "ip_host", "clearly synthetic"),
        ("https://xn--bcher-kva.example/", 1, "punycode", "clearly synthetic"),
        ("https://example.com/%2Fsecure%2Fverify?token=a%2Fb", 1, "percent_encoded", "clearly synthetic"),
        ("https://paypa1.example/account", 1, "typosquatting", "clearly synthetic"),
        ("https://a.b.c.example.com/path", 1, "nested_subdomains", "clearly synthetic"),
        ("https://example.com:8443/login", 1, "unusual_port", "clearly synthetic"),
        ("https://example.com/path?username=admin&password=secret", 1, "embedded_credentials", "clearly synthetic"),
        ("https://example.com/very/long/path?query=1&query=2&nested=3", 0, "complex_legitimate", "clearly synthetic"),
    ]
    frame = pd.DataFrame(rows, columns=["url", "label", "case_category", "source"])
    frame.to_csv(path, index=False)
    return frame
