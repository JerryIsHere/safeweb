"""Translate extracted URL signals into cautious human-readable notes."""

from collections.abc import Mapping


def explain_features(features: Mapping[str, int | float]) -> list[str]:
    """Describe notable signals; none of these signals proves maliciousness."""
    explanations: list[str] = []
    if features.get("url_length", 0) >= 100:
        explanations.append("The URL is unusually long, a signal considered by the model.")
    if features.get("num_subdomains", 0) >= 3:
        explanations.append("The hostname contains several subdomain levels.")
    if features.get("has_ip", 0):
        explanations.append("The hostname is an IP address rather than a domain name.")
    if features.get("num_special_chars", 0) >= 8:
        explanations.append("The URL contains many non-alphanumeric characters.")
    if features.get("url_entropy", 0.0) >= 4.5:
        explanations.append("The URL has relatively high character entropy.")
    keywords = [
        name.removeprefix("keyword_")
        for name, value in features.items()
        if name.startswith("keyword_") and value
    ]
    if keywords:
        explanations.append(
            "The URL contains configured keyword signals: " + ", ".join(keywords) + "."
        )
    if not explanations:
        explanations.append("No configured URL signals stood out; this is not proof of safety.")
    return explanations