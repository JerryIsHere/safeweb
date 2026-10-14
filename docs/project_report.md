# SafeWeb v2.1.0 Project Report

## Summary

SafeWeb is a research prototype that combines an offline PhishVN reference index, a local Random Forest URL assessment, and optional live DNS/metadata/screenshot checks. The static GitHub Pages experience does not require a Flask backend. A result is a warning signal, not a guarantee of safety or maliciousness.

## Dataset

The source is the PhishVN v3.1.0 open archive bundled at the repository root. Its URL table has 53,116 rows, timestamps (`collected_at`, `scraped_at`), label/provenance fields, official grouped train/validation/test partitions, and a companion CompPhish feature table.

Dataset attribution: Thai Nguyen Vu, *PhishVN: A Time-Stamped Vietnamese URL Phishing Dataset with Impersonation-Scenario Labels and Confidence Tiers*, v3.1.0 (2026), DOI [10.17632/b97hxbxtpd.4](https://doi.org/10.17632/b97hxbxtpd.4), CC BY 4.0. Phishing entries include upstream NCSC Tin Nhiem Mang and community/feed sources; source and tier remain in the prepared table.

The reproducible preparation keeps 36,261 canonical URL records after removing 16,855 `www`/apex aliases. No conflicting-label groups or truncated/invalid URLs were observed. Counts after normalization are 25,185 train, 4,452 validation, and 6,624 test (19,909 phishing; 16,352 benign). The upstream partitions have zero shared registrable domains. Source dates and labels remain available for audit; scrape time is not used as event time.

## Features and Model

The model has 52 ordered numeric features: SafeWeb URL/lexical features and 22 PhishVN-derived values, including the 21 CompPhish-aligned features and the suspicious-TLD flag. The supplied feature values were compared against local extraction for every retained row; all 797,742 values matched within floating-point tolerance after matching the upstream definition and domain profile.

A 100-tree Random Forest (`max_depth=16`, `min_samples_leaf=3`, fixed seed) is trained on train plus validation. The grouped temporal test set remains untouched during fitting. Test metrics:

| Metric | Value |
| --- | ---: |
| Accuracy | 0.8752 |
| Phishing precision | 0.8231 |
| Phishing recall | 0.8975 |
| Phishing F1 | 0.8587 |

The confusion matrix in `[benign, phishing]` order is `[[3285, 540], [287, 2512]]`. Database hits are a separate verification stage and are not included in these ML metrics.

## Verification Flow

1. Normalize common user input, including missing schemes and bare names.
2. Compare canonical URL, hostname, and feature signature against the PhishVN index.
3. Run the Random Forest even when a database match exists; display both sources.
4. If the user opts in, query Google DNS-over-HTTPS and request metadata/screenshot data from Microlink, with WordPress mShots as screenshot fallback. Embedded redirect parameters are unwrapped and the final candidate is assessed too.

Live requests are off by default. The URL is shared with external DNS/preview services only after consent. Browser CORS may prevent a complete HTTP redirect chain; SafeWeb reports only observed destinations. HTTPS indicates the URL scheme and is not an independent certificate validation.

## Architecture

- `scripts/prepare_phishvn_dataset.py`: nested archive import, URL canonicalization, deduplication, conflict handling, split audit, and database index.
- `scripts/train_phishvn_model.py`: official partition training and held-out evaluation.
- `src/feature_extractor.py`, `src/predict.py`: Python features, model, and database stage.
- `scripts/export_browser_model.py`: compact trees, public suffix rules, and PhishVN lookup data.
- `web/static/browser-model.js`, `script.js`: local inference, localization, consent-gated live checks, and UI.
- `web/templates/index.html`, `style.css`: responsive three-theme experience.
- `.github/workflows/pages.yml`: main-only GitHub Pages build/deploy.

## Limitations

The metrics describe this dataset and split only; they do not establish real-world effectiveness or calibration. The dataset's source labels, temporal coverage, and class mix can bias results. DNS and metadata providers can fail or return partial information; screenshot services access the destination on the user's behalf. Redirect detection is limited by CORS and provider behavior. SafeWeb is not a browser isolation service and users should not enter credentials into URLs submitted for analysis.
