"""Train and save the initial Random Forest model."""

from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from src.data_loader import class_distribution, load_dataset
from src.feature_extractor import extract_features


RANDOM_STATE = 42
TEST_SIZE = 0.20
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_PATH = PROJECT_ROOT / "data" / "raw" / "urls.csv"
DEFAULT_MODEL_PATH = PROJECT_ROOT / "model" / "random_forest.joblib"


def feature_frame(urls: pd.Series) -> pd.DataFrame:
    """Convert URLs to a consistently ordered numeric feature matrix."""
    return pd.DataFrame([extract_features(url) for url in urls])


def train_model(dataset_path: str | Path, model_path: str | Path) -> dict[str, int]:
    """Train on the training partition and save a portable model bundle."""
    dataset = load_dataset(dataset_path)
    class_counts = dataset["label"].value_counts()
    if len(class_counts) < 2 or class_counts.min() < 2:
        raise ValueError("At least two rows per label are needed for a stratified split.")
    training_rows, testing_rows = train_test_split(
        dataset,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=dataset["label"],
    )
    train_features = feature_frame(training_rows["url"])
    train_labels = training_rows["label"]
    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(train_features, train_labels)
    destination = Path(model_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "feature_names": list(train_features.columns)}, destination)
    return {
        "rows": len(dataset),
        "training_rows": len(train_features),
        "testing_rows": len(testing_rows),
        **class_distribution(dataset),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "dataset",
        type=Path,
        nargs="?",
        default=DEFAULT_DATASET_PATH,
        help=f"CSV with url,label columns (default: {DEFAULT_DATASET_PATH})",
    )
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH)
    arguments = parser.parse_args()
    if not arguments.dataset.is_file():
        parser.error(
            f"dataset not found: {arguments.dataset}. Place a documented CSV with "
            "columns url,label in data/raw/urls.csv, or pass its path explicitly."
        )
    try:
        summary = train_model(arguments.dataset, arguments.model)
    except ValueError as error:
        parser.error(str(error))
    print(f"Trained on {summary['training_rows']} of {summary['rows']} rows.")
    print(f"Class distribution: {summary['legitimate']} legitimate, {summary['phishing']} phishing.")
    print(f"Model saved to {arguments.model}.")


if __name__ == "__main__":
    main()