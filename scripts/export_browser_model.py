"""Export the trained Random Forest and offline suffix rules for browser inference."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_extractor import _DOMAIN_PARSER
from src.predict import DEFAULT_MODEL_PATH, load_model


DEFAULT_OUTPUT = PROJECT_ROOT / "web" / "static" / "model-data.js"


def _ascii_rule(rule: str) -> str:
    prefix = ""
    suffix = rule
    if suffix.startswith("!"):
        prefix, suffix = "!", suffix[1:]
    elif suffix.startswith("*."):
        prefix, suffix = "*.", suffix[2:]
    labels = [label.encode("idna").decode("ascii") for label in suffix.split(".")]
    return prefix + ".".join(labels).lower()


def export_browser_model(model_path: Path, output_path: Path) -> int:
    """Write the model's exact tree splits, leaf probabilities, and PSL rules."""
    bundle = load_model(model_path)
    model = bundle["model"]
    classes = [int(value) for value in model.classes_]
    if classes != [0, 1]:
        raise ValueError(f"Expected model classes [0, 1], got {classes}.")
    positive_index = classes.index(1)

    trees = []
    for estimator in model.estimators_:
        tree = estimator.tree_
        values = tree.value[:, 0, :]
        totals = values.sum(axis=1)
        probabilities = np.divide(
            values[:, positive_index], totals, out=np.zeros_like(totals), where=totals != 0
        )
        trees.append(
            {
                "left": tree.children_left.tolist(),
                "right": tree.children_right.tolist(),
                "feature": tree.feature.tolist(),
                "threshold": tree.threshold.tolist(),
                "positiveProbability": probabilities.tolist(),
            }
        )

    suffix_rules = sorted({_ascii_rule(rule) for rule in _DOMAIN_PARSER.tlds})
    payload = {
        "features": bundle["feature_names"],
        "classes": classes,
        "trees": trees,
        "publicSuffixRules": suffix_rules,
    }
    javascript = "globalThis.safewebModel = " + json.dumps(
        payload, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ) + ";\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(javascript, encoding="utf-8")
    return output_path.stat().st_size


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    size = export_browser_model(arguments.model, arguments.output)
    print(f"Exported browser model to {arguments.output} ({size:,} bytes).")


if __name__ == "__main__":
    main()