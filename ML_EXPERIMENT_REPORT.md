# SafeWeb ML Experiment Report

## Model status

**Decision: B. Improve dataset first.**

The current production Random Forest remains the active model. It is not replaced by the experimental model because the experimental features did not improve any measured metric on the available dataset.

## Scope and constraints

- Production model: `model/random_forest.joblib`
- Experimental model: `model/random_forest_experimental.joblib`
- The experiment preserves the production artifact and trains the experimental model separately.
- The dataset is the bundled synthetic development CSV at `data/raw/urls.csv`.
- The experiment does not claim real-world phishing-detection accuracy.
- The final 0–100 value is a **Risk Score**. It is not a calibrated probability or ML confidence.

## Dataset audit

The audit found 718 rows with 218 legitimate and 500 phishing labels. There were 0 exact duplicate URLs after validation, 126 normalized near-duplicate URL patterns, and 10 overlapping domains between a stratified random training split and test split.

The domain-disjoint evaluation produced a test partition with no overlapping domains or hostname families. The synthetic dataset is strongly separable, so perfect scores on conventional random and domain-disjoint splits are not evidence of real-world performance.

## Experimental design

The experiment compared two models using the same estimator configuration and dataset:

1. Baseline: 30 URL-only features.
2. Experimental: baseline features plus 12 additional deterministic URL-structure features.

Both models used `RandomForestClassifier(n_estimators=200, random_state=42)` and were evaluated on:

- a stratified random 80/20 split,
- a deterministic domain-disjoint 80/20 split,
- the synthetic hard-case suite in `data/hard_case_suite.csv`.

Each result reports accuracy, precision, recall, F1, phishing recall, false-positive rate, false-negative rate, and confusion matrix.

## Results

### Stratified random split

| Model | Accuracy | Precision | Recall | F1 | Phishing recall | FPR | FNR | Confusion matrix |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Baseline | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | `[[44, 0], [0, 100]]` |
| Experimental | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | `[[44, 0], [0, 100]]` |

### Domain-disjoint split

| Model | Accuracy | Precision | Recall | F1 | Phishing recall | FPR | FNR | Confusion matrix |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Baseline | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | `[[74, 0], [0, 70]]` |
| Experimental | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | `[[74, 0], [0, 70]]` |

### Hard-case suite

| Model | Accuracy | Precision | Recall | F1 | Phishing recall | FPR | FNR | Confusion matrix |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Baseline | 0.231 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | `[[3, 0], [10, 0]]` |
| Experimental | 0.231 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | `[[3, 0], [10, 0]]` |

## Conclusion

The experimental features add deterministic signals but do not outperform the production feature set on this synthetic dataset. The experiment confirms that the current model’s perfect benchmark scores arise from strong synthetic separation and are not trustworthy evidence of deployment quality.

The current recommendation is to improve the dataset before changing the model. A suitable next phase requires a documented, labeled URL dataset with source provenance, collection date, labeling policy, and a dedicated validation split that prevents domain or source leakage. The project should also include a held-out time-based or source-disjoint evaluation once such data is available.

## Current production status

- Keep the production Random Forest model.
- Keep the baseline 30-feature schema as the default browser feature set.
- Keep the experimental feature path opt-in and separately documented.
- Do not treat model probability as calibrated confidence.
- Do not deploy this synthetic benchmark as real-world detection evidence.
