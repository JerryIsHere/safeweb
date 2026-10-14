# SafeWeb ML Experiment Report

## Final status

The project is now using a validated 5,000-row PhishVN-compatible dataset and a Random Forest model that remained the strongest performer under the project’s leakage-safe evaluation setup.

The active model is the baseline Random Forest saved in `model/random_forest.joblib`, and the browser bundle in `web/static/model-data.js` was regenerated to match it.

## Scope and constraints

- Dataset source: project-normalized PhishVN-compatible CSV, prepared from the user-provided 5,000-row labeled URL set
- Training path: `scripts/prepare_phishvn_dataset.py` and `scripts/train_phishvn_model.py`
- Model artifact: `model/random_forest.joblib`
- Browser parity check: `scripts/export_browser_model.py` and `scripts/compare_browser_model.py`
- Safety rule: no URLs are visited, opened, or fetched; all processing is string-based and deterministic
- Evaluation rule: the model is measured with a domain-disjoint split to reduce leakage risk

## Dataset audit

The prepared dataset contains exactly 5,000 rows:

- 2,500 benign / 2,500 phishing
- 0 exact duplicates
- 0 near duplicates after normalization
- 1 overlapping domain in the audit summary
- 87 overlapping hostname-family entries in the broader structure audit
- 498 HTTPS URLs
- 0 IP-host URLs
- 6 punycode/IDN URLs
- 315 suspicious-keyword URLs
- 2,498 short phishing URLs

The dataset was normalized in a way that preserves the project’s binary-label contract while accepting the upstream schema variants used by the PhishVN-style source file.

## Model comparison

The project compared the main model candidates under the same feature pipeline and leakage-aware split.

### Domain-disjoint split result

| Model | Accuracy | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: |
| Random Forest | 0.751 | 0.765 | 0.769 | 0.767 |
| Gradient Boosting | lower than Random Forest |  |  |  |

The Random Forest was selected as the active model because it produced the strongest balanced performance while preserving the project’s deterministic tree-based behavior and browser export compatibility.

## Browser parity and deployment status

The browser export was validated against the Python model using fixed sample URLs.

Verified result:

- 10 valid URLs and 6 invalid URLs tested
- max feature delta: 8.88e-16
- max probability delta: 0.0
- parity status: passed

This confirms the exported browser model remains functionally identical to the Python pipeline for the same inputs.

## Production status

Current status is stable and aligned across Python and browser paths:

- Python model artifact: `model/random_forest.joblib`
- Browser bundle: `web/static/model-data.js`
- Frontend inference: `web/static/browser-model.js`
- Full test verification: `npm test` passed

## Evidence summary

The final project state was verified with:

```bash
cd /workspaces/safeweb && source .venv/bin/activate && python scripts/prepare_phishvn_dataset.py --source data/raw/urls_completed.csv --output data/raw/urls.csv
cd /workspaces/safeweb && source .venv/bin/activate && python scripts/prepare_phishvn_dataset.py --source data/raw/urls_completed.csv --output data/raw/PhishVN_training_5000.csv
cd /workspaces/safeweb && source .venv/bin/activate && python scripts/export_browser_model.py --model model/random_forest.joblib --output web/static/model-data.js
cd /workspaces/safeweb && source .venv/bin/activate && python scripts/compare_browser_model.py
cd /workspaces/safeweb && npm test
```

The final verification command passed with:

```text
48 passed in 12.83s
```

## Conclusion

This project now has a clean, validated dataset integration path, a leakage-aware evaluation setup, and a browser-exported model that matches the Python implementation. The Random Forest remains the active production model because it was the best-performing candidate under the project’s safe evaluation protocol.

The project remains a URL-risk prototype, not a calibrated real-world detector, and its conclusions should be interpreted with that scope in mind.
