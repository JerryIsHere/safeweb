# safeweb
hehehehehehhehhheheheheheheheheheheheheheheheheheheheheheheheheehehhe

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

### Web interface

```bash
python run.py
```

The app exposes a health-check endpoint at `GET /health` and a prediction API at `POST /predict` with JSON such as `{"url":"https://example.com"}`. Open `http://127.0.0.1:5000`. Risk boundaries default to 0.35 for MEDIUM and 0.70 for HIGH; override them with `SAFEWEB_MEDIUM_THRESHOLD` and `SAFEWEB_HIGH_THRESHOLD`.

For Render or another WSGI host, run:

```bash
gunicorn wsgi:app --bind 0.0.0.0:$PORT
```

### GitHub Pages deployment

GitHub Pages serves the static interface; it cannot run the Flask app or the Python model. The `pages.yml` workflow exports the interface and deploys it on pushes to `main`. In the repository settings, set **Pages → Build and deployment → Source** to **GitHub Actions**. Without a backend, the interface is published but URL analysis is explicitly unavailable.

To enable analysis, deploy the Flask app and trained model on a separate Python hosting service. Set the repository Actions variable `SAFEWEB_API_URL` to that service's base URL (without a trailing slash). Configure the backend environment variable `SAFEWEB_ALLOWED_ORIGIN` to `https://jerryishere.github.io`; this exact-origin allowlist enables the Pages browser to call `/predict`. The backend must also have the model artifact available. Redeploy the Pages workflow after setting or changing the repository variable.

Run the tests with `python -m pytest`. See `docs/project_report.md`, `docs/poster_content.md`, and `docs/presentation_outline.md` for research materials with experiment results intentionally left as placeholders.

## Architecture

```text
data/
	raw/          Synthetic development demo dataset; replace for research
	processed/    Reproducible derived data (generated; not committed by default)
	sample/       Reserved for clearly labeled development examples
model/          Locally generated model artifacts
reports/        Locally generated evaluation outputs (not bundled)
src/            Data, URL analysis, model, and explanation modules
web/            Flask routes, HTML templates, and static CSS/JavaScript
tests/          Automated behavior tests
config/         Shared project defaults
docs/           Project plan and science-fair materials
```

## Planned Workflow

The intended research workflow is to validate a documented labeled URL dataset, preprocess and split it reproducibly, extract numeric URL/domain features, train the Random Forest on training data, evaluate once on held-out test data, then expose predictions, risk levels, and signal-based explanations through the local Flask interface. The web MVP analyzes URL strings only; it must not visit submitted websites or follow redirects. Model outputs are risk assessments, not proof that a site is safe or malicious. Do not add research data or report metrics until their source and experiment are documented.