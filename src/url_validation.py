"""Normalize and validate URLs before SafeWeb analysis."""

from urllib.parse import urlsplit, urlunsplit


def normalize_url(url: object, *, strip_www: bool = False) -> str:
    """Heal common human input and return a canonical HTTP(S) URL."""
    if not isinstance(url, str) or not url.strip():
        raise ValueError("A non-empty URL string is required.")
    value = url.strip()
    if any(character.isspace() for character in value):
        raise ValueError("The URL must not contain whitespace.")
    if value.startswith("http:/") and not value.startswith(("http://", "https://")):
        raise ValueError("The URL is malformed.")
    if value.startswith("//"):
        value = "https:" + value
    elif "://" not in value:
        host = value.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
        if "." not in host and host.lower() != "localhost":
            value = f"{host}.com{value[len(host):]}"
        value = "https://" + value
    try:
        parts = urlsplit(value)
        hostname = parts.hostname
        port = parts.port
    except ValueError as error:
        raise ValueError("The URL is malformed.") from error
    if parts.scheme.lower() not in {"http", "https"} or not hostname or hostname.lower() in {"http", "https"}:
        raise ValueError("Enter a complete HTTP or HTTPS URL with a hostname.")
    hostname = hostname.lower().rstrip(".")
    if strip_www and hostname.startswith("www."):
        hostname = hostname[4:]
    if not hostname:
        raise ValueError("Enter a complete HTTP or HTTPS URL with a hostname.")
    userinfo = ""
    if parts.username is not None:
        userinfo = parts.username
        if parts.password is not None:
            userinfo += ":" + parts.password
        userinfo += "@"
    authority_host = f"[{hostname}]" if ":" in hostname else hostname
    netloc = userinfo + authority_host
    if port is not None and not (parts.scheme.lower() == "http" and port == 80) and not (
        parts.scheme.lower() == "https" and port == 443
    ):
        netloc += f":{port}"
    path = parts.path.rstrip("/")
    return urlunsplit((parts.scheme.lower(), netloc, path, parts.query, parts.fragment))


def validate_url(url: object) -> str:
    """Return a normalized HTTP(S) URL or raise ValueError with a safe message."""
    return normalize_url(url)