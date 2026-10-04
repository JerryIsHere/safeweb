"""Central configuration for model risk levels."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RiskThresholds:
    """Probability boundaries used to describe the model's risk level."""

    medium: float = 0.35
    high: float = 0.70

    def __post_init__(self) -> None:
        if not 0.0 <= self.medium < self.high <= 1.0:
            raise ValueError("risk thresholds must satisfy 0 <= medium < high <= 1")


def risk_thresholds_from_environment() -> RiskThresholds:
    """Read optional risk boundaries from SAFEWEB_MEDIUM/HIGH_THRESHOLD."""
    return RiskThresholds(
        medium=float(os.getenv("SAFEWEB_MEDIUM_THRESHOLD", "0.35")),
        high=float(os.getenv("SAFEWEB_HIGH_THRESHOLD", "0.70")),
    )


def risk_level(probability: float, thresholds: RiskThresholds | None = None) -> str:
    """Map a phishing probability to LOW, MEDIUM, or HIGH risk."""
    selected = thresholds or RiskThresholds()
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be between 0 and 1")
    if probability >= selected.high:
        return "HIGH"
    if probability >= selected.medium:
        return "MEDIUM"
    return "LOW"