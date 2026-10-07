"""Central configuration for model risk levels."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RiskThresholds:
    """Probability boundaries used to describe the model's risk level."""

    low: float = 0.25
    medium: float = 0.50
    high: float = 0.75

    def __post_init__(self) -> None:
        if not 0.0 <= self.low < self.medium < self.high <= 1.0:
            raise ValueError("risk thresholds must satisfy 0 <= low < medium < high <= 1")

    def classify(self, probability: float) -> str:
        """Map phishing probability to a human-readable risk label."""
        if not 0.0 <= probability <= 1.0:
            raise ValueError("probability must be between 0 and 1")
        if probability >= self.high:
            return "VERY HIGH"
        if probability >= self.medium:
            return "HIGH"
        if probability >= self.low:
            return "CAUTION"
        return "LOW"


def risk_thresholds_from_environment() -> RiskThresholds:
    """Read optional risk boundaries from SAFEWEB_LOW/MEDIUM/HIGH_THRESHOLD."""
    return RiskThresholds(
        low=float(os.getenv("SAFEWEB_LOW_THRESHOLD", "0.25")),
        medium=float(os.getenv("SAFEWEB_MEDIUM_THRESHOLD", "0.50")),
        high=float(os.getenv("SAFEWEB_HIGH_THRESHOLD", "0.75")),
    )


def risk_level(probability: float, thresholds: RiskThresholds | None = None) -> str:
    """Map a phishing probability to the SafeWeb four-tier risk scale."""
    selected = thresholds or RiskThresholds()
    return selected.classify(probability)