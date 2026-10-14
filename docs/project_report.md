# SafeWeb v2.3.0 Project Report

## Summary

SafeWeb is a research prototype that combines an offline PhishVN reference index, four local URL classifiers, an interactive PhishVN explorer, and optional live DNS/metadata/screenshot checks. The static GitHub Pages experience does not require a Flask backend. A result is a warning signal, not a guarantee of safety or maliciousness.

## Dataset

The source is the PhishVN v3.1.0 open archive bundled at the repository root. Its URL table has 53,116 rows, timestamps (`collected_at`, `scraped_at`), label/provenance fields, official grouped train/validation/test partitions, and a companion CompPhish feature table.

Dataset attribution: Thai Nguyen Vu, *PhishVN: A Time-Stamped Vietnamese URL Phishing Dataset with Impersonation-Scenario Labels and Confidence Tiers*, v3.1.0 (2026), DOI [10.17632/b97hxbxtpd.4](https://doi.org/10.17632/b97hxbxtpd.4), CC BY 4.0. Phishing entries include upstream NCSC Tin Nhiem Mang and community/feed sources; source and tier remain in the prepared table.

The reproducible preparation keeps 36,261 canonical URL records after removing 16,855 `www`/apex aliases. No conflicting-label groups or truncated/invalid URLs were observed. Counts after normalization are 25,185 train, 4,452 validation, and 6,624 test (19,909 phishing; 16,352 benign). The upstream partitions have zero shared registrable domains. Source dates and labels remain available for audit; scrape time is not used as event time.

## Features and Model

The model has 52 ordered numeric features: SafeWeb URL/lexical features and 22 PhishVN-derived values, including the 21 CompPhish-aligned features and the suspicious-TLD flag. The supplied feature values were compared against local extraction for every retained row; all 797,742 values matched within floating-point tolerance after matching the upstream definition and domain profile.

Random Forest, Gradient Boosting, sigmoid-calibrated linear SVM, and scaled Logistic Regression use the same 52-feature schema. Each is fit on train plus validation (29,637 rows) and evaluated on the untouched domain-disjoint test set (6,624 rows). Precision, recall, and F1 refer to the phishing class; confusion counts are TN/FP/FN/TP.

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | TN / FP / FN / TP |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Random Forest | 0.8752 | 0.8231 | 0.8975 | 0.8587 | 0.9466 | 3285 / 540 / 287 / 2512 |
| Gradient Boosting | 0.8798 | 0.8008 | 0.9525 | 0.8701 | 0.9495 | 3162 / 663 / 133 / 2666 |
| Linear SVM (calibrated) | 0.8798 | 0.8054 | 0.9436 | 0.8690 | 0.9456 | 3187 / 638 / 158 / 2641 |
| Logistic Regression | 0.8631 | 0.8326 | 0.8460 | 0.8393 | 0.9440 | 3349 / 476 / 431 / 2368 |

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
