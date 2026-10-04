
## SafeWeb Research Prototype

SafeWeb is an educational prototype that estimates whether URL characteristics resemble patterns in a labeled phishing dataset. It analyzes URL text only: it does not open submitted URLs, follow redirects, download files, or contact websites. A model result is a risk signal, not proof that a site is safe or malicious.

### Setup

Use Python 3.11 or newer, then install the dependencies from the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows, activate the environment with `.venv\\Scripts\\activate`.

### Dataset and model

`data/raw/urls.csv` is synthetic development demo data. It is useful for exercising the training pipeline and web interface, but it is not research data and cannot establish real-world phishing detection performance. Do not present metrics from this file as real-world results or research findings. For research, replace it with a documented dataset and record its source, license, collection date, and labeling method.

The CSV must contain these required columns:

| Column | Required values |
| --- | --- |
| `url` | A non-empty URL string |
| `label` | `0` for legitimate or `1` for phishing |

The default command reads `data/raw/urls.csv`, or you can pass another CSV path explicitly. Training validates HTTP(S) URLs and binary labels, reports invalid or conflicting rows clearly, removes exact duplicate URLs, and fits the Random Forest on the reproducible 80% training partition only. Evaluation recreates the isolated 20% test partition and writes metrics, a classification report, confusion matrix, feature importance, and error analysis under `reports/`. Any metrics generated from the bundled synthetic demo data are for pipeline verification only.

```bash
python -m src.train
python -m src.evaluate data/raw/urls.csv
```

### Local development

```bash
python run.py
```

The Flask app is retained for local development and Python-side comparisons. It exposes `GET /health` and `POST /predict`; the production GitHub Pages frontend does not call either route. The browser frontend extracts features and runs the model locally. Python risk boundaries default to 0.35 for MEDIUM and 0.70 for HIGH; override them with `SAFEWEB_MEDIUM_THRESHOLD` and `SAFEWEB_HIGH_THRESHOLD` when using the development backend.

The browser model is exported from the trained scikit-learn artifact with:

```bash
python scripts/export_browser_model.py
python scripts/compare_browser_model.py
```

### GitHub Pages deployment

The `pages.yml` workflow builds and deploys a fully static application on pushes to `main`. In repository settings, set **Pages → Build and deployment → Source** to **GitHub Actions**. The page-relative asset paths support project URLs such as `https://jerryishere.github.io/safeweb/`.

`web/static/model-data.js` contains the exported Random Forest trees and offline public-suffix rules required by the browser. It is generated from the actual trained model; after retraining, regenerate and commit the browser artifact. Once the page and static assets finish loading, URL analysis uses no network requests, opens no submitted URL, and requires no Python, Flask, Render service, or prediction API.

Run the browser tests with `npm run test:browser`, the Python tests with `python -m pytest`, and direct model parity checks with `python scripts/compare_browser_model.py` when the local Python model artifact is available. See `docs/project_report.md`, `docs/poster_content.md`, and `docs/presentation_outline.md` for research materials with experiment results intentionally left as placeholders.

## Architecture

```text
data/
	raw/          Synthetic development demo dataset; replace for research
	processed/    Reproducible derived data (generated; not committed by default)
	sample/       Reserved for clearly labeled development examples
model/          Locally generated Python model artifacts (not deployed)
reports/        Locally generated evaluation outputs (not bundled)
src/            Data, URL analysis, model, and explanation modules
web/            Flask development routes, shared template, and static browser app/model
scripts/        Static-site build, browser-model export, and parity validation
tests/          Automated behavior tests
config/         Shared project defaults
docs/           Project plan and science-fair materials
```

## Planned Workflow

The intended research workflow is to validate a documented labeled URL dataset, preprocess and split it reproducibly, extract numeric URL/domain features, train the Random Forest on training data, evaluate once on held-out test data, then expose predictions, risk levels, and signal-based explanations through the local Flask interface. The web MVP analyzes URL strings only; it must not visit submitted websites or follow redirects. Model outputs are risk assessments, not proof that a site is safe or malicious. Do not add research data or report metrics until their source and experiment are documented.