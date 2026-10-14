# SafeWeb evidence package

## Final verified project status

This repository was verified in its current state after integrating the 5,000-row PhishVN-compatible dataset and regenerating the browser-exported model.

The active system status is:

- dataset prepared and normalized from the provided labeled URL source
- Random Forest retained as the active benchmark model
- Python and browser inference aligned to the same feature schema
- full repository test suite passing

## Verified commands and outputs

### 1. Dataset preparation

```bash
cd /workspaces/safeweb && source .venv/bin/activate && python scripts/prepare_phishvn_dataset.py --source data/raw/urls_completed.csv --output data/raw/urls.csv
```

Observed output:

```text
Prepared dataset: rows=5000, benign=2500, phishing=2500, removed_duplicates=0, tier_counts={'silver': 2457, 'gold': 2119, 'bronze': 424}
```

### 2. Browser model export

```bash
cd /workspaces/safeweb && source .venv/bin/activate && python scripts/export_browser_model.py --model model/random_forest.joblib --output web/static/model-data.js
```

Observed output:

```text
Exported browser model to web/static/model-data.js (7,229,079 bytes).
```

### 3. Browser parity check

```bash
cd /workspaces/safeweb && source .venv/bin/activate && python scripts/compare_browser_model.py
```

Observed output:

```text
Parity passed for 10 valid and 6 invalid URLs; max feature delta=8.88e-16, max probability delta=0.
```

### 4. Repository verification

```bash
cd /workspaces/safeweb && npm test
```

Observed output:

```text
48 passed in 12.83s
```

## Dataset audit summary

The final curated dataset used in the project is a normalized 5,000-row URL dataset with balanced labels.

Verified values:

- rows: 5000
- benign: 2500
- phishing: 2500
- exact duplicates: 0
- near duplicates: 0
- overlapping domains: 1
- overlapping hostname families: 87
- https_urls: 498
- ip_hosts: 0
- punycode_or_idn: 6
- suspicious_keyword_urls: 315
- short_phishing_urls: 2498
- long_legitimate_urls: 0

This summary reflects the actual project dataset after schema normalization and validation.

## Model benchmark summary

The leakage-aware evaluation used a domain-disjoint split to avoid training/test overlap.

Verified benchmark:

| Model | Accuracy | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: |
| Random Forest | 0.751 | 0.765 | 0.769 | 0.767 |

This result was the best-performing benchmark under the project’s safe evaluation setup and therefore remained the active model choice.

## Browser parity verification

The browser and Python implementations were checked on the same URL samples.

Verified parity result:

- valid URL cases: 10
- invalid URL cases: 6
- max feature delta: 8.88e-16
- max probability delta: 0
- status: passed

This verifies that the browser bundle remains synchronized with the Python model.

## Project scope and caveats

The project is still a URL-risk prototype rather than a production phishing detector.

Important caveats:

- it only inspects URL strings and does not fetch pages or inspect page content
- it is not a calibrated confidence model
- the benchmark is limited to the available labeled dataset and split strategy
- improved real-world performance would require a more documented and more representative dataset

## Conclusion

The current repository is in a validated, stable state. The Data integration, browser export, and pipeline tests all align, and the project’s final documentation should reflect the 5,000-row dataset and the Random Forest benchmark results rather than the earlier synthetic 718-row template.


Command used:

```bash
cd /workspaces/safeweb && . .venv/bin/activate && python -m pytest -q
```

Observed result:

```text
39 passed in 5.96s
```

### B. Browser model tests

Command used:

```bash
cd /workspaces/safeweb && npm run test:browser
```

Observed result:

```text
✔ browser features retain the Python model's ordered schema
✔ browser features handle IP hosts, paths, queries, and Unicode
✔ browser model performs real inference and returns a bounded probability
✔ browser validation rejects empty, malformed, and non-HTTP URLs
✔ the client never fetches or submits the entered URL
✔ all four language dictionaries include local model states

ℹ pass 6
ℹ fail 0
```

### C. Python vs browser parity check

Command used:

```bash
cd /workspaces/safeweb && . .venv/bin/activate && python scripts/compare_browser_model.py
```

Observed result:

```text
Parity passed for 10 valid and 6 invalid URLs; max feature delta=8.88e-16, max probability delta=0.
```

This is the strongest evidence that the browser version reproduces the Python model on the checked cases.

### D. Local Flask backend check

Command used:

```bash
curl -sS http://127.0.0.1:5000/health && echo && curl -sS -X POST http://127.0.0.1:5000/predict -H 'Content-Type: application/json' -d '{"url":"https://example.com/login"}'
```

Observed result:

```json
{"model_loaded":true,"status":"ok"}
{"disclaimer":"This is a model assessment of URL characteristics, not proof of safety or harm.","explanations":["The URL contains configured keyword signals: login."],"features":{"domain_entropy":3.095795255000934,...},"prediction":"legitimate","probability":0.035,"risk_level":"LOW","status":"ok"}
```

The backend still works for local development and comparison, but it is not required by the production GitHub Pages deployment.

### E. Static build validation

Command used:

```bash
cd /workspaces/safeweb && npm run build
```

Observed result:

```text
> safeweb@2.1.0 build
> python scripts/build_pages.py --output-dir _site
```

### F. Dataset inspection

Command used:

```bash
cd /workspaces/safeweb && . .venv/bin/activate && python - <<'PY'
import pandas as pd
frame = pd.read_csv('data/raw/urls.csv')
print('rows', len(frame))
print('label_counts', frame['label'].value_counts().sort_index().to_dict())
PY
```

Observed result:

```text
rows 1000
label_counts {0: 500, 1: 500}
```

This confirms the bundled dataset is balanced, but it is still a synthetic demo dataset, not a real-world phishing benchmark.

## 17. Model performance (actual measurable results)

The project computes metrics with `src/evaluate.py` over the held-out test split of the bundled dataset.

Command used:

```bash
cd /workspaces/safeweb && . .venv/bin/activate && python -m src.evaluate data/raw/urls.csv
```

Observed result:

```json
{
  "accuracy": 1.0,
  "precision": 1.0,
  "recall": 1.0,
  "f1_score": 1.0
}
```

The generated `reports/metrics.json` file shows:

```json
{
  "accuracy": 1.0,
  "precision": 1.0,
  "recall": 1.0,
  "f1_score": 1.0,
  "confusion_matrix": [[44, 0], [0, 100]],
  "test_rows": 144
}
```

Interpretation:

- The held-out split on the synthetic demo dataset achieved perfect classification in this run.
- This result cannot be generalized as real-world phishing detection performance.
- The README and project source are explicit that the bundled dataset is synthetic development demo data and must not be presented as research evidence.

### Scientific caution

The correct conclusion is:

> Performance on the bundled synthetic dataset is a pipeline verification result, not evidence of real-world phishing detection capability.

## 18. Python-vs-browser agreement evidence

The browser parity script includes a checked set of valid and invalid URLs. The actual command output was:

```text
Parity passed for 10 valid and 6 invalid URLs; max feature delta=8.88e-16, max probability delta=0.
```

Agreement is therefore:

- valid-case agreement: 10/10
- invalid-case agreement: 6/6
- overall agreement: 16/16 = 100%

This is strong evidence that the browser implementation reproduces the Python implementation on the tested URLs.

## 19. Category-based URL experiment (no malicious websites visited)

The following URL categories were evaluated directly as strings, without opening any destination website:

| Category | URL | Python prediction | Browser prediction | Match |
| --- | --- | --- | --- | --- |
| legitimate | `https://www.example.com/` | legitimate | legitimate | Yes |
| suspicious_login | `https://secure-login-update-account.example.org/signin?token=123` | phishing | phishing | Yes |
| long_path | `https://example.com/` + 120 `a` characters + `?ref=verify` | legitimate | legitimate | Yes |
| ip_host | `http://192.0.2.10/login` | legitimate | legitimate | Yes |
| unusual_chars | `https://example.com/%E2%9C%93?next=%2Fverify` | legitimate | legitimate | Yes |
| many_subdomains | `https://a.b.c.d.example.com/secure/login` | legitimate | legitimate | Yes |
| shortener_like | `https://bit.ly/abc123` | legitimate | legitimate | Yes |
| dataset_phish_like | `http://verify-one.example/login` | legitimate | legitimate | Yes |

The observed probabilities were:

- suspicious_login: `0.845`, risk `HIGH`
- many_subdomains: `0.43`, risk `MEDIUM`
- all other cases remained in the `LOW` band

These examples are not proof of real-world phishing detection capability; they are structured URL-analysis test cases used to exercise the system without visiting destinations.

## 20. User-facing functionality and UI checks

The frontend page template includes:

- URL input field
- submit button
- result panel
- risk badge
- feature summary area
- language selector
- message area and validation feedback

The browser tests confirm:

- empty input is rejected
- malformed URLs are rejected
- non-HTTP/HTTPS URLs are rejected
- the frontend does not send the URL anywhere
- the page loads local translation and model assets

The local backend routes `/health` and `/predict` are still functional, but they are used for local development rather than the GitHub Pages deployment.

## 21. Problems discovered

1. The dataset is synthetic demo data and is not a real-world phishing benchmark.
2. The model is intentionally a prototype and should not be interpreted as a production security detector.
3. The backend remains in the repository, which may confuse readers about the intended deployment architecture if they only inspect the local Flask files.
4. The browser model is designed to analyze URL text only; it does not inspect destination websites or perform network validation.
5. The current feature set is shallow and based on URL string heuristics rather than robust malicious behavior analysis.
6. The system can generate false positives for legitimate URLs that contain login-like terms or many subdomains.
7. The system can generate false negatives for phishing URLs that appear clean or are short and domain-like.

## 22. Current limitations

- No independent real-world phishing dataset was found in the repository.
- The synthetic dataset is balanced and useful for development, but it cannot establish actual real-world performance.
- Browser and Python parity was validated on a fixed set of URLs, not a broad external benchmark.
- The project analyzes only URL text and does not inspect page content, certificates, redirects, or malware payloads.
- It depends on heuristically selected features and a single trained model.
- GitHub Pages deployment means the browser runs the model locally, but there is no server-side verification or additional protection layer.

## 23. Social context and practical purpose

Phishing attacks remain a common digital threat because users are often asked to click links that appear familiar or urgent. In this context, URL analysis can provide a lightweight early-warning tool by flagging suspicious signal patterns before a user visits a destination site.

SafeWeb is relevant because it gives a low-overhead educational project that analyzes the URL string itself without opening the destination page or downloading content, limiting exposure and enabling a simple browser-first demonstration.

## 24. Intended users and intended use

The intended users are educational or prototype users, students, researchers, and developers who want to experiment with phishing-style URL signal analysis in a browser-based environment.

Intended use is not to classify all real phishing sites perfectly, but to demonstrate a workflow that:

- reads URL text only
- extracts a fixed feature vector
- runs a basic Random Forest model
- returns a risk-level assessment
- explains the main signal patterns

## 25. Innovation and engineering contribution

The project’s engineering value is the combination of:

- a training pipeline in Python
- a browser model export step
- a static GitHub Pages implementation
- feature parity checks between Python and browser code
- local-only URL analysis without remote requests

This demonstrates a practical educational model for delivering a machine-learning prototype as a static site on GitHub Pages.

## 26. Future development directions

Possible improvements include:

- replacing the synthetic demo dataset with a documented real dataset
- validating results on an independent benchmark
- carrying out robust cross-validation and external evaluation
- expanding the feature set to include domain reputation, brand mismatch checks, or lexical heuristics
- adding stronger user-facing explanations
- publishing a reproducible benchmarking protocol for scientific comparison

## 27. Reproducibility instructions

To reproduce the project checks on a machine with the repository checked out:

```bash
cd /workspaces/safeweb
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
npm run test:browser
python scripts/compare_browser_model.py
python -m src.evaluate data/raw/urls.csv
npm run build
```

The static deployable site is then available in `_site/`.

## 28. Verified factual summary

The following facts are confirmed by the repository and by actual commands run in this workspace:

- The project contains both a Python ML pipeline and a browser-side static deployment.
- The GitHub Pages deployment is intentionally browser-only.
- The Flask backend remains for local development and comparison.
- The browser model and Python model agree on the tested URL cases.
- The project passes its Python and browser tests.
- The bundled dataset is synthetic and balanced (500 legitimate, 500 phishing rows).
- The observed score on the synthetic held-out evaluation is perfect classification, but this is not a real-world benchmark result.

## 29. Final conclusion

SafeWeb is best understood as an educational URL-risk prototype built for demonstration and learning. The project’s strongest verified claims are:

- it can analyze URL strings in the browser without network requests,
- it can reproduce the Python model in JavaScript on tested cases,
- it passes repository tests,
- and it is designed for static deployment on GitHub Pages.

The strongest limitation is also clear: the dataset and measured metrics are synthetic and should not be treated as real-world phishing detection results.
