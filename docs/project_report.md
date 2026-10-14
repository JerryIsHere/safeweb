# SafeWeb v2.3.0 Project Report

## Summary

SafeWeb is a research prototype that combines an offline PhishVN reference index, four local URL classifiers, an interactive PhishVN explorer, and optional live DNS/metadata/screenshot checks. The static GitHub Pages experience does not require a Flask backend. A result is a warning signal, not a guarantee of safety or maliciousness.

## Dataset

The source is the PhishVN v3.1.0 open archive bundled at the repository root. Its URL table has 53,116 rows, timestamps (`collected_at`, `scraped_at`), label/provenance fields, official grouped train/validation/test partitions, and a companion CompPhish feature table.

Dataset attribution: Thai Nguyen Vu, *PhishVN: A Time-Stamped Vietnamese URL Phishing Dataset with Impersonation-Scenario Labels and Confidence Tiers*, v3.1.0 (2026), DOI [10.17632/b97hxbxtpd.4](https://doi.org/10.17632/b97hxbxtpd.4), CC BY 4.0. Phishing entries include upstream NCSC Tin Nhiem Mang and community/feed sources; source and tier remain in the prepared table.

The reproducible preparation keeps 36,261 canonical URL records after removing 16,855 `www`/apex aliases. No conflicting-label groups or truncated/invalid URLs were observed. Counts after normalization are 25,185 train, 4,452 validation, and 6,624 test (19,909 phishing; 16,352 benign). The upstream partitions have zero shared registrable domains. Source dates and labels remain available for audit; scrape time is not used as event time.

## Features and Model

The model has 55 ordered numeric features: 30 SafeWeb URL/lexical features, 22 PhishVN-derived values, and three reproducible PhiUSIIL URL obfuscation features (flag, encoded-character count, and ratio). The 21 supplied CompPhish values matched local extraction across 36,261 retained PhishVN rows.

Random Forest, Gradient Boosting, sigmoid-calibrated linear SVM, and scaled Logistic Regression use the same 55-feature schema. Fit uses 29,637 PhishVN train+validation rows plus 231,662 cleaned PhiUSIIL rows (261,299 total); PhiUSIIL rows sharing any held-out PhishVN test domain are excluded. Each source receives equal total sample weight, balanced between benign/phishing within source. Evaluation remains on the untouched, domain-disjoint 6,624-row PhishVN test set. Precision, recall, and F1 refer to phishing; confusion counts are TN/FP/FN/TP.

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | TN / FP / FN / TP |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Random Forest | 0.8745 | 0.8075 | 0.9232 | 0.8615 | 0.9426 | 3209 / 616 / 215 / 2584 |
| Gradient Boosting | 0.8789 | 0.7976 | 0.9561 | 0.8697 | 0.9436 | 3146 / 679 / 123 / 2676 |
| Linear SVM (calibrated) | 0.5805 | 1.0000 | 0.0071 | 0.0142 | 0.9308 | 3825 / 0 / 2779 / 20 |
| Logistic Regression | 0.8555 | 0.7996 | 0.8782 | 0.8371 | 0.9330 | 3209 / 616 / 341 / 2458 |

The SVM's current threshold detects only 20 of 2,799 phishing test URLs (recall 0.0071) despite ROC-AUC 0.9308; its individual verdict is not useful until calibration or thresholding is improved.

The current SVM decision threshold is not useful for phishing recall despite its ROC-AUC: it detects only 20 of 2,799 phishing test URLs. Its calibration/threshold needs further work before relying on its individual verdict.

Confusion matrices are recorded per model in `reports/phishvn_domain_eval.json`; their counts are in `[benign, phishing]` order. Database hits are a separate verification stage and are not included in these ML metrics.

## Verification Flow

1. Normalize common user input, including missing schemes and bare names.
2. Compare canonical URL, hostname, and feature signature against the PhishVN index.
3. Run all four models even when a database match exists; show the direct database label separately from each model score and the ensemble average.
4. If the user opts in, query Google DNS-over-HTTPS and request metadata/screenshot data from Microlink, with WordPress mShots as screenshot fallback. Embedded redirect parameters are unwrapped and the final candidate is assessed too.

Live requests are off by default. The URL is shared with external DNS/preview services only after consent. Browser CORS may prevent a complete HTTP redirect chain; SafeWeb reports only observed destinations. HTTPS indicates the URL scheme and is not an independent certificate validation.

## Architecture

- `scripts/prepare_phishvn_dataset.py`: nested archive import, URL canonicalization, deduplication, conflict handling, split audit, and database index.
- `scripts/train_phishvn_model.py`: shared official partition training and held-out evaluation for all four classifiers.
- `src/feature_extractor.py`, `src/predict.py`: Python features, model, and database stage.
- `scripts/export_browser_model.py`: trees and calibrated linear coefficients, public suffix rules, and PhishVN lookup/explorer data.
- `web/static/browser-model.js`, `script.js`: local inference, localization, consent-gated live checks, and UI.
- `web/templates/index.html`, `style.css`: responsive three-theme experience.
- `.github/workflows/pages.yml`: main-only GitHub Pages build/deploy.

## Limitations

The metrics describe this dataset and split only; they do not establish real-world effectiveness or calibration. The dataset's source labels, temporal coverage, and class mix can bias results. DNS and metadata providers can fail or return partial information; screenshot services access the destination on the user's behalf. Redirect detection is limited by CORS and provider behavior. SafeWeb is not a browser isolation service and users should not enter credentials into URLs submitted for analysis.
