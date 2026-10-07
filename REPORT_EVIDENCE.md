# SafeWeb evidence package

## 1. Project overview

SafeWeb is a URL-analysis prototype designed to estimate whether URL characteristics resemble patterns associated with phishing or legitimate examples. The project combines a Python training/evaluation workflow with a browser-side static deployment on GitHub Pages. The actual production architecture is browser-only for the deployed site, while the Flask app in `web/app.py` remains as a local development and comparison backend.

The project is explicitly framed as an educational prototype rather than a production phishing detector. The README and source files warn that model results are risk signals and not proof that a URL is safe or malicious.

## 2. Verified architecture

### Actual current implementation

The project uses two parallel execution paths:

1. Python pipeline for training, validation, evaluation, and backend comparison.
2. Browser-side static inference for the GitHub Pages site.

Using the repository implementation as the source of truth:

- `src/train.py` trains a `RandomForestClassifier` on URL features.
- `src/evaluate.py` re-creates the isolated 20% test partition and computes metrics.
- `src/predict.py` loads the saved model bundle and predicts a risk label and probability.
- `web/app.py` exposes local Flask endpoints `/health` and `/predict` for development/testing.
- `scripts/export_browser_model.py` converts the trained model into `web/static/model-data.js`.
- `web/static/browser-model.js` runs the same feature extraction and tree-based inference in the browser.
- `scripts/build_pages.py` creates the static `_site` output that is deployed to GitHub Pages.
- `.github/workflows/pages.yml` builds and deploys the static site.

### Production vs local backend

The repository clearly distinguishes the production deployment from the local development backend:

- The GitHub Pages workflow checks for `/predict`, `localhost`, and backend-specific references in the built static output and fails the build if such references are present.
- The browser JavaScript tests assert that the browser client does not use `fetch()`, `XMLHttpRequest`, or `sendBeacon()`.
- The static page loads `model-data.js`, `browser-model.js`, and `translations.js` directly without any API endpoint.

This means the deployed GitHub Pages site is intended to function entirely in the browser with no remote API dependency.

## 3. Important files and project structure

| File/Folder | Type | Purpose | Importance | Used in production? |
| --- | --- | --- | --- | --- |
| `src/train.py` | Python | Trains the Random Forest model from CSV data and saves the artifact. | High | No |
| `src/evaluate.py` | Python | Evaluates the held-out test split and produces metrics and charts. | High | No |
| `src/predict.py` | Python | Loads the model bundle and predicts a class/probability from a URL string. | High | No |
| `src/feature_extractor.py` | Python | Extracts numeric URL features without network access. | High | Yes, mirrored in browser |
| `src/url_validation.py` | Python | Validates URL format and rejects invalid/non-HTTP inputs. | High | Yes, mirrored in browser |
| `src/data_loader.py` | Python | Loads the dataset, validates columns, strips duplicates, and checks labels. | High | No |
| `web/app.py` | Python/Flask | Local development API and page rendering. | Medium | No, local-only |
| `web/templates/index.html` | HTML | User-facing page layout and static asset includes. | High | Yes |
| `web/static/browser-model.js` | JavaScript | Browser inference logic and validation. | High | Yes |
| `web/static/script.js` | JavaScript | Frontend interaction, i18n, result rendering, and submission logic. | High | Yes |
| `web/static/model-data.js` | JavaScript | Exported Random Forest tree data and public-suffix rules. | High | Yes |
| `scripts/export_browser_model.py` | Python | Converts the trained Python model into browser-safe JS data. | High | Yes, in build/deploy pipeline |
| `scripts/build_pages.py` | Python | Builds the static GitHub Pages artifact. | High | Yes |
| `scripts/compare_browser_model.py` | Python | Verifies JavaScript and Python inference parity on fixed URL samples. | High | No |
| `model/random_forest.joblib` | Binary model artifact | Saved trained model bundle used by Python code. | High | No |
| `data/raw/urls.csv` | Dataset | Synthetic demo dataset used for training and evaluation. | High | No, demo-only |
| `.github/workflows/pages.yml` | GitHub Actions workflow | Builds and deploys the static site to GitHub Pages. | High | Yes |
| `README.md` | Documentation | Project overview and usage instructions. | Medium | Documentation only |
| `docs/` | Documentation | Research notes and project-planning materials. | Medium | Documentation only |

## 4. Machine-learning model and storage

The model is a `RandomForestClassifier` from scikit-learn, trained in `src/train.py` with these settings:

- `n_estimators=200`
- `random_state=42`
- train/test split with `test_size=0.20`
- `stratify=dataset["label"]`

The trained bundle is saved to `model/random_forest.joblib` using `joblib.dump(...)`.

The saved bundle includes:

- `model`: trained scikit-learn model
- `feature_names`: the ordered feature list used to build the training matrix

`src/predict.py` validates that the bundle contains the required fields before predicting.

## 5. Feature extraction logic

The feature extractor in `src/feature_extractor.py` computes numeric URL signals without making network requests. The extracted features include:

- URL length
- domain length
- path/query lengths
- counts of dots, slashes, hyphens, underscores, digits, letters, and special characters
- `has_https`
- `has_ip`
- number of subdomains
- presence of `@`, `?`, `=`, `%`, and double slashes
- URL entropy and domain entropy
- keyword indicators such as `login`, `signin`, `verify`, `account`, `password`, `bank`, `payment`, and `confirm`

The browser model uses a mirrored implementation in `web/static/browser-model.js` to reproduce the same feature schema and inference behavior.

## 6. Frontend structure

The production frontend is assembled from:

- `web/templates/index.html` for the page scaffold
- `web/static/style.css` for layout and styling
- `web/static/translations.js` for localization text
- `web/static/model-data.js` for the exported Random Forest data and PSL rules
- `web/static/browser-model.js` for validation and inference
- `web/static/script.js` for UI interactions and result rendering

Browser tests explicitly confirm that the client never uses `fetch()`, `XMLHttpRequest`, or `sendBeacon()` and therefore never sends the entered URL anywhere.

## 7. Browser-side inference logic

Browser inference is implemented in `web/static/browser-model.js`.

It does the following:

- validates the input URL (rejects empty strings, whitespace, malformed URLs, non-HTTP/HTTPS URLs)
- extracts the same features as Python
- loads the exported model from `globalThis.safewebModel`
- walks the decision trees and computes `probability`
- maps probability to `LOW`, `MEDIUM`, or `HIGH`
- returns feature values and explanation strings

This is the critical piece that allows GitHub Pages deployment without a Python backend.

## 8. Remaining backend/server code

The repository still contains local server-side code:

- `run.py` starts the Flask app on `127.0.0.1:5000`
- `wsgi.py` is the WSGI entry point for local Flask development
- `web/app.py` defines the Flask app and routes

This backend is not required for the production GitHub Pages deployment. It is retained for local development, testing, and Python-side comparisons.

## 9. Configuration files

Important configuration files include:

- `requirements.txt` — Python dependency list
- `package.json` — scripts for build/test
- `.github/workflows/pages.yml` — GitHub Pages deployment workflow
- `config/config.yaml` — project configuration defaults

## 10. Dataset and training files

The default dataset is `data/raw/urls.csv`.

The project checks this dataset for:

- required columns `url` and `label`
- invalid URLs
- missing labels
- binary labels only (`0` or `1`)
- duplicate URLs with conflicting labels
- exact duplicate URLs removed before training

The README explicitly warns that this is synthetic demo data and should not be treated as real-world phishing-detection research data.

## 11. GitHub Pages deployment configuration

The deployment workflow is `.github/workflows/pages.yml`.

It:

- checks out the repository
- sets up Node 22 and Python 3.11
- runs browser tests
- builds the static site with `npm run build`
- verifies that the built output contains the expected static files
- rejects backend-like references such as `/predict`, `localhost`, or `render.com`
- uploads the artifact and deploys to GitHub Pages

The build step explicitly enforces the static-pages architecture.

## 12. GitHub Actions workflows

There are two workflow files in `.github/workflows/`:

- `pages.yml` — deploy static site
- `blank.yml` — repository placeholder workflow

The active production deployment is driven by `pages.yml`.

## 13. Important assets and model files

- `model/random_forest.joblib` — saved model bundle
- `web/static/model-data.js` — exported Random Forest trees and public-domain suffix rules
- `web/static/browser-model.js` — browser prediction logic
- `_site/` — generated static build artifact
- `reports/` — evaluation outputs produced by `src/evaluate.py`

## 14. README and documentation

The project documentation describes the intended educational prototype workflow and explicitly warns against treating synthetic demo metrics as real research findings. The README is useful for understanding the intended system, but the actual implementation is the final source of truth.

## 15. Evidence from repository inspection

### Repository-level checks

Searches across the repo found local Flask and backend references in development files such as `web/app.py`, `run.py`, `wsgi.py`, and `src/predict.py`, which is expected for local development. However, the built static artifact in `_site` is checked to ensure these backend references are absent.

### Command used for the static output check

```bash
cd /workspaces/safeweb && grep -R -nE 'SAFEWEB_API_URL|SAFEWEB_ALLOWED_ORIGIN|safeweb-api-url|apiBaseUrl|/predict|localhost|render\.com' _site || true && echo '---' && test -s _site/index.html && test -s _site/static/style.css && test -s _site/static/translations.js && test -s _site/static/browser-model.js && test -s _site/static/model-data.js && echo 'pages_static_assets_ok'
```

Output observed:

```text
---
pages_static_assets_ok
```

This confirms that the built artifact contains the expected static files and no backend-specific references.

## 16. Experiments performed

### A. Python test suite

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
