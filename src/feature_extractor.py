"""Deterministic, string-only URL feature extraction."""

from __future__ import annotations

import ipaddress
import math
import re
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


def _hostname_depth(hostname: str) -> int:
    if not hostname or _is_ip(hostname):
        return 0
    return len([label for label in hostname.split(".") if label])


def _percent_encoding_count(url: str) -> int:
    return len(re.findall(r"%[0-9A-Fa-f]{2}", url))


def _username_password_count(url: str) -> int:
    parsed = _split_url(url)
    if not parsed.netloc or "@" not in parsed.netloc:
        return 0
    authority = parsed.netloc.rsplit("@", 1)[0]
    return int(":" in authority)


def _port_count(url: str) -> int:
    parsed = _split_url(url)
    try:
        return int(parsed.port is not None)
    except ValueError:
        return 0


def _repeated_characters(url: str) -> int:
    return int(any(character * 3 in url for character in set(url)))


def _digit_to_letter_ratio(url: str) -> float:
    letters = sum(character.isalpha() for character in url)
    digits = sum(character.isdigit() for character in url)
    if letters == 0:
        return float(digits)
    return digits / letters


def _digit_ratio(url: str) -> float:
    total = len(url)
    return 0.0 if total == 0 else sum(character.isdigit() for character in url) / total


def _special_char_ratio(url: str) -> float:
    total = len(url)
    return 0.0 if total == 0 else sum(not character.isalnum() for character in url) / total


def _query_parameter_count(url: str) -> int:
    return len([part for part in _split_url(url).query.split("&") if part])


def _repeated_query_keys(url: str) -> int:
    query = _split_url(url).query
    if not query:
        return 0
    keys = []
    for pair in query.split("&"):
        if "=" in pair:
            keys.append(pair.split("=", 1)[0])
    return int(sum(count > 1 for count in Counter(keys).values()))


def _hostname_token_count(hostname: str) -> int:
    if not hostname:
        return 0
    return len([token for token in re.split(r"[^a-z0-9]+", hostname.lower()) if token])


def _has_punycode_or_idn(hostname: str) -> int:
    if not hostname:
        return 0
    try:
        ascii_hostname = hostname.encode("idna").decode("ascii")
    except UnicodeError:
        return 0
    return int(hostname != ascii_hostname or hostname.startswith("xn--"))


def _base_features(url: str, parts: SplitResult, hostname: str) -> dict[str, int | float]:
    return {
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


def extract_features(url: str, *, include_experimental: bool = False) -> dict[str, int | float]:
    """Extract baseline features or the opt-in experimental feature schema."""
    if not isinstance(url, str):
        raise TypeError("url must be a string")
    if not url.strip():
        raise ValueError("url must not be empty")

    parts = _split_url(url)
    hostname = _hostname(parts)
    lowered = url.lower()
    features = _base_features(url, parts, hostname)
    features.update({f"keyword_{keyword}": int(keyword in lowered) for keyword in _KEYWORDS})

    if not include_experimental:
        return features

    experimental = {
        "digit_to_letter_ratio": _digit_to_letter_ratio(url),
        "digit_ratio": _digit_ratio(url),
        "special_char_ratio": _special_char_ratio(url),
        "query_parameter_count": _query_parameter_count(url),
        "hostname_depth": _hostname_depth(hostname),
        "has_punycode_or_idn": _has_punycode_or_idn(hostname),
        "percent_encoding_count": _percent_encoding_count(url),
        "has_repeated_characters": _repeated_characters(url),
        "has_username_password": _username_password_count(url),
        "has_unusual_port": _port_count(url),
        "hostname_token_count": _hostname_token_count(hostname),
        "repeated_query_keys": _repeated_query_keys(url),
    }
    features.update(experimental)
    return features


BASELINE_FEATURE_ORDER = tuple(_base_features("https://example.com", _split_url("https://example.com"), "example.com").keys())
EXPERIMENTAL_FEATURE_ORDER = BASELINE_FEATURE_ORDER + (
    "digit_to_letter_ratio",
    "digit_ratio",
    "special_char_ratio",
    "query_parameter_count",
    "hostname_depth",
    "has_punycode_or_idn",
    "percent_encoding_count",
    "has_repeated_characters",
    "has_username_password",
    "has_unusual_port",
    "hostname_token_count",
    "repeated_query_keys",
)