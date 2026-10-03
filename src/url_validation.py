"""Validation for URLs analyzed as strings only."""

from urllib.parse import urlsplit


def validate_url(url: object) -> str:
    """Return a trimmed HTTP(S) URL or raise ValueError with a safe message."""
    if not isinstance(url, str) or not url.strip():
        raise ValueError("A non-empty URL string is required.")
    value = url.strip()
    if any(character.isspace() for character in value):
        raise ValueError("The URL must not contain whitespace.")
    try:
        parts = urlsplit(value)
        hostname = parts.hostname
        parts.port
    except ValueError as error:
        raise ValueError("The URL is malformed.") from error
    if parts.scheme.lower() not in {"http", "https"} or not hostname:
        raise ValueError("Enter a complete HTTP or HTTPS URL with a hostname.")
    return value