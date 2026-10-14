"""Deterministic, string-only URL feature extraction."""

from __future__ import annotations

import ipaddress
import math
import re
from collections import Counter
from collections.abc import Mapping
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
PHISHVN_FEATURE_NAMES = (
    "phishvn_url_len",
    "phishvn_dom_len",
    "phishvn_is_ip",
    "phishvn_tld_len",
    "phishvn_subdom_cnt",
    "phishvn_letter_cnt",
    "phishvn_digit_cnt",
    "phishvn_special_cnt",
    "phishvn_eq_cnt",
    "phishvn_qm_cnt",
    "phishvn_amp_cnt",
    "phishvn_dot_cnt",
    "phishvn_dash_cnt",
    "phishvn_under_cnt",
    "phishvn_letter_ratio",
    "phishvn_digit_ratio",
    "phishvn_spec_ratio",
    "phishvn_slash_cnt",
    "phishvn_entropy",
    "phishvn_path_len",
    "phishvn_query_len",
    "phishvn_suspicious_tld",
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


def _phiusiil_obfuscation_features(url: str) -> dict[str, int | float]:
    """Compute PhiUSIIL's URL-only percent-encoding obfuscation signals."""
    encoded_character_count = 3 * _percent_encoding_count(url)
    return {
        "phiusiil_has_obfuscation": int(encoded_character_count > 0),
        "phiusiil_obfuscated_char_count": encoded_character_count,
        "phiusiil_obfuscation_ratio": encoded_character_count / len(url) if url else 0.0,
    }


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


def _phishvn_features(
    url: str,
    parts: SplitResult,
    hostname: str,
    domain_profile: Mapping[str, int | float] | None = None,
    suspicious_tlds: set[str] | None = None,
) -> dict[str, int | float]:
    """Compute the CompPhish-aligned features supplied with PhishVN."""
    scheme_stripped = re.sub(r"^https?://", "", url, flags=re.IGNORECASE)
    extracted = _DOMAIN_PARSER(hostname) if hostname else None
    registrable = (
        (extracted.top_domain_under_public_suffix or hostname)
        if extracted is not None
        else ""
    )
    tld = extracted.suffix if extracted is not None else ""
    letters = sum(character.isalpha() for character in scheme_stripped)
    digits = sum(character.isdigit() for character in scheme_stripped)
    length = len(scheme_stripped)
    profile = domain_profile or {}
    tld_labels = suspicious_tlds or set()
    return {
        "phishvn_url_len": length,
        "phishvn_dom_len": profile.get("phishvn_dom_len", len(registrable)),
        "phishvn_is_ip": int(_is_ip(hostname)),
        "phishvn_tld_len": profile.get("phishvn_tld_len", len(tld)),
        "phishvn_subdom_cnt": profile.get("phishvn_subdom_cnt", _subdomain_count(hostname)),
        "phishvn_letter_cnt": letters,
        "phishvn_digit_cnt": digits,
        "phishvn_special_cnt": length - letters - digits,
        "phishvn_eq_cnt": scheme_stripped.count("="),
        "phishvn_qm_cnt": scheme_stripped.count("?"),
        "phishvn_amp_cnt": scheme_stripped.count("&"),
        "phishvn_dot_cnt": scheme_stripped.count("."),
        "phishvn_dash_cnt": scheme_stripped.count("-"),
        "phishvn_under_cnt": scheme_stripped.count("_"),
        "phishvn_letter_ratio": letters / length if length else 0.0,
        "phishvn_digit_ratio": digits / length if length else 0.0,
        "phishvn_spec_ratio": (length - letters - digits) / length if length else 0.0,
        "phishvn_slash_cnt": scheme_stripped.count("/"),
        "phishvn_entropy": _entropy(scheme_stripped),
        "phishvn_path_len": len(parts.path.strip("/")),
        "phishvn_query_len": len(parts.query),
        "phishvn_suspicious_tld": profile.get(
            "phishvn_suspicious_tld",
            int(bool(tld) and tld.lower() in tld_labels),
        ),
    }


def extract_features(
    url: str,
    *,
    include_experimental: bool = False,
    domain_profile: Mapping[str, int | float] | None = None,
    suspicious_tlds: set[str] | None = None,
) -> dict[str, int | float]:
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
    features.update(_phishvn_features(url, parts, hostname, domain_profile, suspicious_tlds))
    features.update(_phiusiil_obfuscation_features(url))

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


BASELINE_FEATURE_ORDER = (
    *tuple(_base_features("https://example.com", _split_url("https://example.com"), "example.com").keys()),
    *(f"keyword_{keyword}" for keyword in _KEYWORDS),
    *PHISHVN_FEATURE_NAMES,
)
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