# SafeWeb v2.3.0 ML Experiment Report

## Objective and protocol

The experiment compares Random Forest, Gradient Boosting, calibrated linear SVM, and Logistic Regression using PhishVN v3.1.0 and PhiUSIIL. Fit uses PhishVN train+validation plus PhiUSIIL rows whose registrable domains do not occur in the held-out PhishVN test set. Evaluation remains on the same untouched official PhishVN test partition.

## Source data and preparation

- Source: `PhishVN A Time-Stamped Vietnamese URL Phishing Dat.zip`, nested `PhishVN_v3.1.0_open.zip`.
- Additional training source: `data/raw/phiusiil+phishing+url+dataset.zip`; source labels were inverted to SafeWeb's phishing-positive convention.
- Attribution/license: Thai Nguyen Vu, PhishVN v3.1.0 (2026), DOI [10.17632/b97hxbxtpd.4](https://doi.org/10.17632/b97hxbxtpd.4), CC BY 4.0.
- Archive source rows: 53,116.
- Canonical retained rows: 36,261 (19,909 phishing, 16,352 benign).
- Alias duplicates removed: 16,855 (mostly `www`/apex variants).
- Conflicting normalized URL labels removed: 0.
- Invalid/truncated URL rows removed: 0.
- Split counts after canonical deduplication: 25,185 train; 4,452 validation; 6,624 test.
- Registrable-domain intersections among all three splits: 0.

The fit also uses the 235,795-row PhiUSIIL URL dataset (`URL`, `label`); source labels are inverted to SafeWeb's `1=phishing` convention. Cleaning removes 86 rows with conflicting normalized URL labels, 3,586 canonical duplicates, and 461 rows on PhishVN test domains, retaining 231,662 training rows. The separate source archive is read-only. Collection/scrape times in PhishVN remain provenance, not labels.

## Feature schema

The models consume 55 numeric columns: 30 SafeWeb URL/keyword features, 21 pre-extracted CompPhish-aligned features, the PhishVN suspicious-TLD flag, and three PhiUSIIL URL-only obfuscation features (percent-encoding flag/count/ratio). All 797,742 PhishVN feature values matched upstream within `1e-8`.

## Models

- Random Forest: 100 trees, maximum depth 16, minimum leaf 3, balanced-subsample weighting.
- Gradient Boosting: 100 trees, learning rate 0.1, depth 3.
- SVM: `StandardScaler` + `LinearSVC`, sigmoid calibration with 3-fold cross-validation.
- Logistic Regression: `StandardScaler` + `LogisticRegression`.
- Random seed: 42. Each model fits on the same 261,299 rows with equal total source weights and equal class weight within each source; all use the same 6,624-row PhishVN test set.

## Held-out results

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | TN / FP / FN / TP |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Random Forest | 0.8745 | 0.8075 | 0.9232 | 0.8615 | 0.9426 | 3209 / 616 / 215 / 2584 |
| Gradient Boosting | 0.8789 | 0.7976 | 0.9561 | 0.8697 | 0.9436 | 3146 / 679 / 123 / 2676 |
| Calibrated SVM | 0.5805 | 1.0000 | 0.0071 | 0.0142 | 0.9308 | 3825 / 0 / 2779 / 20 |
| Logistic Regression | 0.8555 | 0.7996 | 0.8782 | 0.8371 | 0.9330 | 3209 / 616 / 341 / 2458 |

The calibrated SVM's default threshold found only 20 of 2,799 phishing test URLs despite its ROC-AUC of 0.9308. Treat its current verdict as unusable until its calibration/threshold is revised.

Confusion matrices use `[benign, phishing]` label order:

```text
RF `[[3209, 616], [215, 2584]]`; GB `[[3146, 679], [123, 2676]]`; SVM `[[3825, 0], [2779, 20]]`; LR `[[3209, 616], [341, 2458]]`.
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
