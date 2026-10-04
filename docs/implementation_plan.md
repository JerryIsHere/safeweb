# SafeWeb Implementation Plan

## Repository Snapshot

The root project currently contains `src/`, `web/`, `tests/`, and `docs/`, along with `requirements.txt`, `run.py`, and `.gitignore`. The `data/` directory contains only `data/model/src/app.py` and `data/model/src/requirements.txt`; both nested files are empty. There is no research CSV, saved model, generated report, or root `config/`, `model/`, or `reports/` directory.

### Existing Code

- `src/data_loader.py`: validates `url,label`, handles missing/invalid labels, duplicate URLs, and class counts.
- `src/feature_extractor.py`: deterministic string-only features, IP detection, tldextract-based subdomain counts, and Shannon entropy.
- `src/train.py`: reproducible stratified split and `RandomForestClassifier(n_estimators=200, random_state=42)` fit on the training partition.
- `src/evaluate.py`: standard metrics, confusion matrix, feature importance, classification report, and error-analysis output for the held-out partition.
- `src/predict.py`, `src/explain.py`, and `src/config.py`: model loading, prediction, cautious signal explanations, and environment-configurable risk thresholds.
- `web/app.py`, `web/templates/`, and `web/static/`: Flask `GET /`, JSON `POST /predict`, and the browser interface.
- `tests/`: data, feature, model, prediction, and Flask tests. `docs/`: report, poster, and presentation templates with unrun-result placeholders.

### Dependencies

The root dependency manifest declares Flask, joblib, matplotlib, numpy, pandas, pytest, scikit-learn, and tldextract. `data/model/src/requirements.txt` is empty; avoid maintaining a second dependency list unless that nested tree is deliberately adopted.

### Conflicts and Gaps

- The proposed `src/preprocess.py` and `config/` directory do not exist. Split constants currently live in `src/train.py`; risk thresholds are configured through `src/config.py` and environment variables.
- The empty nested `data/model/src/app.py` conflicts by name with the active `web/app.py`. Decide whether the nested files are legacy placeholders or intended entry points before moving or deleting anything.
- `README.md` is modified in the worktree and includes pre-existing text; preserve its contents when making later documentation edits.
- The feature test for entropy currently compares a value with itself. Replace that assertion with an independently checkable expected property during the testing phase.
- No real dataset or trained artifact is present. Training and research metrics remain pending user-provided, documented data.

### Preservation Rules

Preserve `README.md`, `data/model/src/app.py`, `data/model/src/requirements.txt`, and all current root additions (`.gitignore`, root `requirements.txt`, `run.py`, `src/`, `web/`, `tests/`, and `docs/`). Do not replace nested placeholders, remove files, create research data, or commit generated model/report artifacts as part of planning.

## Phased Implementation Plan

This is a plan for subsequent work, not authorization to implement these phases now. Existing work is identified so later tasks can extend it rather than replace it unnecessarily.

### 1. Project Setup

- **Objective:** Confirm the root layout as canonical, ensure a reproducible Python setup, and resolve the role of the empty nested `data/model/src/` placeholders before moving or deleting anything.
- **Files involved:** Existing `requirements.txt`, `.gitignore`, `run.py`, `README.md`, `src/`, `web/`, `tests/`, `docs/`; assess `data/model/src/app.py` and `data/model/src/requirements.txt`. Create `config/`, `model/`, or `reports/` only when the owning phase needs them.
- **Dependencies:** Python 3.11+; root requirements include Flask, joblib, matplotlib, numpy, pandas, pytest, scikit-learn, and tldextract. Do not establish a second dependency manifest without deciding to use the nested tree.
- **Expected output:** A documented root project layout and setup instructions, no duplicate app/dependency source of truth, and generated artifacts ignored appropriately.
- **Manual verification:** Create/activate a clean virtual environment, install with `python -m pip install -r requirements.txt`, inspect `git status --short`, and confirm both nested placeholders remain intact until their purpose is decided.

### 2. Dataset Loading and Preprocessing

- **Objective:** Load documented `url,label` CSV data, validate required values and binary labels, remove exact duplicate URLs, report class counts, and define a reproducible stratified split without using test data during training.
- **Files involved:** Existing `src/data_loader.py` and `src/train.py`; consider `src/preprocess.py` only if it owns distinct preprocessing rather than duplicating loader or trainer logic. Add or extend `tests/test_data_pipeline.py`.
- **Dependencies:** pandas; scikit-learn's `train_test_split`; pytest for tests.
- **Expected output:** Validated rows and class distribution; clear errors for missing/empty URLs, missing or invalid labels, conflicting duplicate labels, and insufficient class sizes. Split settings remain explicit (`test_size=0.20`, `random_state=42`, stratified by label).
- **Manual verification:** Use a separately documented dataset supplied by the project owner; inspect pre/post duplicate counts and class distribution. Check invalid CSV cases with temporary files. Do not add invented or demo rows to the research dataset.

### 3. URL Feature Extraction

- **Objective:** Maintain deterministic, numeric, fixed-schema URL/domain features using string parsing only; parse IP addresses and subdomains robustly and calculate Shannon entropy.
- **Files involved:** Existing `src/feature_extractor.py`; `tests/test_feature_extractor.py`.
- **Dependencies:** Python standard library (`urllib.parse`, `ipaddress`, `math`, `collections`) and tldextract; tldextract must be configured not to fetch data at runtime.
- **Expected output:** `extract_features(url)` returns consistent feature names and numeric values, rejects empty input, and handles malformed strings without network access. Signals, including keywords and HTTPS, are not treated as proof.
- **Manual verification:** Try normal HTTP/HTTPS URLs, IPv4/IPv6 hosts, `@`, queries, multiple subdomains, keywords, and malformed URL text. Confirm repeat calls match and no request is made. Replace the current entropy test that compares a value with itself with a known-value or independently checked property.

### 4. Model Training

- **Objective:** Fit the specified binary classifier exclusively on the training partition and persist a portable model bundle with its feature ordering.
- **Files involved:** Existing `src/train.py`, `src/feature_extractor.py`, `src/data_loader.py`; model output under the ignored root `model/` directory; `tests/test_model_pipeline.py`.
- **Dependencies:** pandas, scikit-learn (`RandomForestClassifier`, `train_test_split`), joblib, and the feature extractor.
- **Expected output:** A saved `RandomForestClassifier(n_estimators=200, random_state=42)` bundle and a training summary. The test partition remains unused for fitting or tuning.
- **Manual verification:** Train on a project-owner-provided, documented dataset, inspect the saved artifact location and training row count, and confirm repeat runs with the fixed split and seed follow the same procedure. Use temporary fixtures only for software tests, never as reported research results.

### 5. Evaluation and Error Analysis

- **Objective:** Evaluate the trained artifact against the isolated held-out partition, report the required metrics, and expose individual TP/TN/FP/FN cases.
- **Files involved:** Existing `src/evaluate.py`, `src/train.py`, `src/data_loader.py`; output under ignored root `reports/`; `tests/test_model_pipeline.py`.
- **Dependencies:** scikit-learn metrics, pandas, matplotlib, numpy, joblib, and the trained model plus the exact documented dataset/split procedure.
- **Expected output:** Machine-readable metrics JSON, classification report, confusion matrix image, feature-importance image, and error-analysis CSV. Accuracy, precision, recall, and F1 must be computed, never hard-coded.
- **Manual verification:** Run evaluation only after training, inspect the confusion matrix label orientation and TP/TN/FP/FN rows, and verify each test example appears once. Record metrics only from the research experiment; otherwise retain `[EXPERIMENT NOT RUN]`.

### 6. Prediction and Explanation

- **Objective:** Validate an HTTP(S) URL string, load a compatible model bundle, return a class and phishing probability, map it to centralized risk thresholds, and explain relevant URL signals cautiously.
- **Files involved:** Existing `src/predict.py`, `src/url_validation.py`, `src/config.py`, `src/explain.py`, `src/feature_extractor.py`; prediction tests in `tests/test_model_pipeline.py` and related focused tests.
- **Dependencies:** joblib, pandas, model bundle, feature extraction, and configured risk thresholds.
- **Expected output:** A structured result containing prediction, probability, LOW/MEDIUM/HIGH risk level, features, explanations, and a non-absolute disclaimer. Missing or incompatible model artifacts fail clearly.
- **Manual verification:** Test valid and invalid URLs, missing/corrupt or incompatible artifacts, both labels, and probabilities around each configured threshold. Confirm no result says a website is absolutely safe or malicious.

### 7. Flask Backend

- **Objective:** Provide the local page route and JSON prediction endpoint with input validation, stable response shapes, appropriate status codes, and safe failures.
- **Files involved:** Existing `web/app.py`; `tests/test_web_app.py`; model and URL-validation modules under `src/`.
- **Dependencies:** Flask and the prediction/validation layer; a trained model artifact is optional for starting the app but required for successful prediction.
- **Expected output:** `GET /` renders the interface; `POST /predict` accepts `{"url":"..."}` and responds with the structured assessment or a consistent JSON error. The backend does not visit URLs, follow redirects, or log submitted URL contents.
- **Manual verification:** Start with `python run.py`; use the Flask test client or a local HTTP client to exercise valid JSON, non-JSON, missing/empty URL, malformed URL, absent model, and prediction success when a real model exists. Confirm errors contain no stack trace.

### 8. Frontend

- **Objective:** Provide an accessible vanilla HTML/CSS/JavaScript interface for URL submission, risk display, observed signals, extracted features, and validation/model error states.
- **Files involved:** Existing `web/templates/index.html`, `web/static/style.css`, and `web/static/script.js`.
- **Dependencies:** Flask-served static/template files and the browser Fetch API; no frontend framework is required.
- **Expected output:** A usable responsive interface whose wording describes model assessments and warning levels, not certainty. Submitted input is sent only to the local SafeWeb API.
- **Manual verification:** Open the local app at desktop and mobile widths; inspect keyboard use, focus, loading, API error, model-unavailable, and successful-result states. Verify no horizontal overflow and that no user-entered URL is sent to a third-party service.

### 9. Testing

- **Objective:** Verify data, feature, training/evaluation, prediction, and API behavior with deterministic tests while separating software fixtures from research data.
- **Files involved:** Existing `tests/test_data_pipeline.py`, `tests/test_feature_extractor.py`, `tests/test_model_pipeline.py`, `tests/test_web_app.py`; add narrow tests alongside the owning module as gaps are addressed.
- **Dependencies:** pytest and the root runtime dependencies. Tests that train models should use temporary paths and clearly synthetic fixtures only to test code behavior.
- **Expected output:** A passing test suite covering normal/malformed/empty URLs, feature consistency, data validation, model artifact handling, metrics output, and Flask response contracts. No test output is presented as research performance.
- **Manual verification:** Run `python -m pytest` in the configured project environment; review actual failures and diagnostics rather than assuming success. Separately perform the UI checks in Phase 8.

### 10. Documentation

- **Objective:** Explain setup, architecture, dataset provenance, experiment protocol, results, limitations, and presentation materials while preserving scientific integrity.
- **Files involved:** Existing `README.md`, `docs/project_report.md`, `docs/poster_content.md`, and `docs/presentation_outline.md`; this `docs/implementation_plan.md` records the plan.
- **Dependencies:** Verified project behavior, the selected dataset's source/license/labeling details, and actual experiment artifacts before reporting results.
- **Expected output:** Coherent setup/use instructions and complete research materials. Unknown dataset details and unrun metrics remain explicitly marked TODO or `[EXPERIMENT NOT RUN]`.
- **Manual verification:** Follow setup and usage instructions from a clean environment; compare documented commands and paths with the actual project. Check each scientific statement against source information and generated evaluation outputs. Preserve existing README text when updating it.

### 11. Final Cleanup

- **Objective:** Review project consistency, portability, generated artifacts, security boundaries, and final user-visible claims without expanding scope.
- **Files involved:** All changed project files; `.gitignore`; generated `model/` and `reports/` outputs; `README.md` and `docs/`.
- **Dependencies:** Python environment and tools used by the preceding phases; git status/diff for worktree review.
- **Expected output:** No accidental dataset/model/report artifacts committed, no machine-specific paths or duplicate configuration sources, clean diagnostics, and documentation that accurately distinguishes completed work from TODOs.
- **Manual verification:** Review `git status --short` and the final diff, run the full test suite, inspect the running app if available, confirm submitted URLs are not contacted, and ensure no metrics or claims were fabricated. Do not discard or overwrite pre-existing worktree changes.

## Assumptions

- The root `src/` and `web/` layout is the intended canonical application structure.
- No research dataset or trained model is available yet; neither will be invented.
- The MVP remains URL-string-only and makes no network requests to submitted URLs.
- The nested empty files are preserved until their intended role is confirmed.