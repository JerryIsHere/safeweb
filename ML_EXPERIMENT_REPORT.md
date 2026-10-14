# SafeWeb v2.3.0 ML Experiment Report

## Objective and protocol

The experiment compares Random Forest, Gradient Boosting, calibrated linear SVM, and Logistic Regression on the PhishVN v3.1.0 open URL dataset. All four use the same URL-derived feature matrix and the same official train/validation/test partitions grouped by registrable domain. Fit uses train plus validation; the official test partition remains untouched.

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

## Models

- Random Forest: 100 trees, maximum depth 16, minimum leaf 3, balanced-subsample weighting.
- Gradient Boosting: 100 trees, learning rate 0.1, depth 3.
- SVM: `StandardScaler` + `LinearSVC`, sigmoid calibration with 3-fold cross-validation.
- Logistic Regression: `StandardScaler` + balanced `LogisticRegression`.
- Random seed: 42. All models fit on 29,637 rows and tested on the same 6,624 rows.

## Held-out results

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | TN / FP / FN / TP |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Random Forest | 0.8752 | 0.8231 | 0.8975 | 0.8587 | 0.9466 | 3285 / 540 / 287 / 2512 |
| Gradient Boosting | 0.8798 | 0.8008 | 0.9525 | 0.8701 | 0.9495 | 3162 / 663 / 133 / 2666 |
| Calibrated SVM | 0.8798 | 0.8054 | 0.9436 | 0.8690 | 0.9456 | 3187 / 638 / 158 / 2641 |
| Logistic Regression | 0.8631 | 0.8326 | 0.8460 | 0.8393 | 0.9440 | 3349 / 476 / 431 / 2368 |

Confusion matrices use `[benign, phishing]` label order:

```text
RF `[[3285, 540], [287, 2512]]`; GB `[[3162, 663], [133, 2666]]`; SVM `[[3187, 638], [158, 2641]]`; LR `[[3349, 476], [431, 2368]]`.
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
