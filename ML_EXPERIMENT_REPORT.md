# SafeWeb v2.1.0 ML Experiment Report

## Objective and protocol

The experiment tests whether a Random Forest can distinguish the labels in the PhishVN v3.1.0 open URL dataset using URL-derived features. The released train/validation/test partitions are already grouped and temporally organized by registrable domain. SafeWeb trains on train plus validation and holds the official test partition out of fitting.

## Source data and preparation

- Source: `PhishVN A Time-Stamped Vietnamese URL Phishing Dat.zip`, nested `PhishVN_v3.1.0_open.zip`.
- Attribution/license: Thai Nguyen Vu, PhishVN v3.1.0 (2026), DOI [10.17632/b97hxbxtpd.4](https://doi.org/10.17632/b97hxbxtpd.4), CC BY 4.0.
- Archive source rows: 53,116.
- Canonical retained rows: 36,261 (19,909 phishing, 16,352 benign).
- Alias duplicates removed: 16,855 (mostly `www`/apex variants).
- Conflicting normalized URL labels removed: 0.
- Invalid/truncated URL rows removed: 0.
- Split counts after canonical deduplication: 25,185 train; 4,452 validation; 6,624 test.
- Registrable-domain intersections among all three splits: 0.

The release includes `collected_at` and `scraped_at`; collection time is retained as provenance, while scrape time is not used as an event timestamp. The original archive is never modified. Generated clean CSV is in ignored `data/processed/`.

## Feature schema

The model consumes 52 numeric columns: 30 SafeWeb URL/keyword features plus 21 pre-extracted CompPhish-aligned features and the PhishVN suspicious-TLD flag. The source includes the same 21 CompPhish values in a companion table. After URL and host normalization, all 797,742 retained-row feature values matched the upstream values within `1e-8`; host-specific PhishVN profiles retain the release's domain/TLD boundaries where its PSL differs from the bundled parser.

## Model

- Estimator: `RandomForestClassifier`
- Trees: 100
- Maximum depth: 16
- Minimum samples per leaf: 3
- Random seed: 42
- Training rows: 29,637 (train plus validation)
- Test rows: 6,624, never used to fit the estimator
- Class weighting: `balanced_subsample`

## Held-out results

| Metric | Phishing class | Overall |
| --- | ---: | ---: |
| Accuracy | — | 0.8752 |
| Precision | 0.8231 | — |
| Recall | 0.8975 | — |
| F1 | 0.8587 | — |

Confusion matrix in `[benign, phishing]` label order:

```text
[[3285, 540],
 [ 287, 2512]]
```

Test support is 3,825 benign and 2,799 phishing. These scores are dataset/split-specific and are not calibrated confidence or estimates of deployment-wide performance.

## Reference database versus ML

The browser/backend reference index is built from the cleaned PhishVN records: 19,909 known phishing URL keys, 19,859 exclusive phishing hosts, and 4,461 feature signatures that do not collide with a benign label. Database hits are shown as provenance and can override the user-facing verdict; they are not included in the held-out ML metrics above.

## Reproduction

```bash
source .venv/bin/activate
python scripts/prepare_phishvn_dataset.py
python scripts/train_phishvn_model.py
python scripts/export_browser_model.py
python scripts/compare_browser_model.py
```

The Python artifact is written locally to `model/random_forest.joblib` (ignored by Git); the deployable compact model/index bundle is `web/static/model-data.js`.
