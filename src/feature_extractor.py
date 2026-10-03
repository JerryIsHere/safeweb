"""Deterministic, string-only URL feature extraction."""

from __future__ import annotations

import ipaddress
import math
from collections import Counter
from urllib.parse import SplitResult, urlsplit

import tldextract


_DOMAIN_PARSER = tldextract.TLDExtract(suffix_list_urls=())
_KEYWORDS = (
    "login",
    "signin",
    "verify",
    "account",
    "password",
    "bank",
    "payment",
    "confirm",
)


def _entropy(value: str) -> float:
    """Return Shannon entropy in bits per character."""
    if not value:
        return 0.0
    counts = Counter(value)
    length = len(value)
    return -sum((count / length) * math.log2(count / length) for count in counts.values())


def _split_url(url: str) -> SplitResult:
    """Parse a URL without allowing malformed bracket syntax to escape."""
    try:
        return urlsplit(url)
    except ValueError:
        return SplitResult("", "", "", "", "")


def _hostname(parts: SplitResult) -> str:
    try:
        return (parts.hostname or "").lower().rstrip(".")
    except ValueError:
        return ""


def _is_ip(hostname: str) -> bool:
    if not hostname:
        return False
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        return False


def _subdomain_count(hostname: str) -> int:
    if not hostname or _is_ip(hostname):
        return 0
    extracted = _DOMAIN_PARSER(hostname)
    return len([label for label in extracted.subdomain.split(".") if label])


def extract_features(url: str) -> dict[str, int | float]:
    """Extract numeric URL signals without making a network request.

    Empty strings are rejected. Other malformed strings are handled as URL
    text and produce the same fixed feature schema as valid URLs.
    """
    if not isinstance(url, str):
        raise TypeError("url must be a string")
    if not url.strip():
        raise ValueError("url must not be empty")

    parts = _split_url(url)
    hostname = _hostname(parts)
    lowered = url.lower()
    features: dict[str, int | float] = {
        "url_length": len(url),
        "domain_length": len(hostname),
        "path_length": len(parts.path),
        "query_length": len(parts.query),
        "num_dots": url.count("."),
        "num_slashes": url.count("/"),
        "num_hyphens": url.count("-"),
        "num_underscores": url.count("_"),
        "num_digits": sum(character.isdigit() for character in url),
        "num_letters": sum(character.isalpha() for character in url),
        "num_special_chars": sum(not character.isalnum() for character in url),
        "has_https": int(parts.scheme.lower() == "https"),
        "has_ip": int(_is_ip(hostname)),
        "num_subdomains": _subdomain_count(hostname),
        "has_at": int("@" in url),
        "has_question_mark": int("?" in url),
        "has_equals": int("=" in url),
        "has_percent": int("%" in url),
        "has_double_slash": int("//" in url.split("://", 1)[-1]),
        "has_query": int(bool(parts.query)),
        "url_entropy": _entropy(url),
        "domain_entropy": _entropy(hostname),
    }
    features.update({f"keyword_{keyword}": int(keyword in lowered) for keyword in _KEYWORDS})
    return features