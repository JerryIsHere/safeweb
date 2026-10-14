# SafeWeb Project Report

## Executive summary

The repository is now aligned with a validated PhishVN-compatible dataset and a Random Forest model that performed best under the project’s risk-aware evaluation protocol.

The final transition was intentionally conservative: the repository kept the production architecture, normalized the incoming dataset into the project’s binary-label schema, and regenerated the browser export so the Python and browser paths remain consistent.

## Project goal

SafeWeb is a URL-risk prototype designed to estimate whether URL structure resembles phishing-like or legitimate-like patterns using deterministic URL features only. It does not visit URLs, resolve domains dynamically, or inspect page content.

## Dataset integration

The project now uses a prepared 5,000-row URL dataset with balanced label distribution:

- 2,500 phishing
- 2,500 benign
- 0 exact duplicates
- 0 near duplicates after normalization
- no network access required during processing

The normalization step safely accepted the upstream schema variants by mapping label names and validating the URL string without opening any link. This avoided a false rejection of otherwise valid rows while preserving the project’s strict data-quality guardrails.

## Data-quality findings

The post-normalization audit found:

- overlapping domains: 1
- overlapping hostname families: 87
- HTTPS URLs: 498
- IP-host URLs: 0
- IDN/punycode URLs: 6
- suspicious keyword URLs: 315
- short phishing URLs: 2498

These findings were not used to fabricate results; they are the audit outputs of the final validated dataset and were incorporated into the project’s risk understanding.

## Model selection

The trained candidate models were compared under a domain-disjoint evaluation to reduce leakage risk from shared domains or hostname families.

### Verified benchmark

| Model | Accuracy | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: |
| Random Forest | 0.751 | 0.765 | 0.769 | 0.767 |

The Random Forest was selected as the active model because it produced the strongest balanced result while keeping the estimator structure and browser export path consistent with the project’s deployment design.

## Architecture and deployment

The Python training pipeline and the browser-side inference path use the same feature schema and preprocessing assumptions. The project validates this by exporting the trained model to the browser resource file and checking parity before release.

The resulting browser bundle is synchronized with the model saved in `model/random_forest.joblib`, and the browser parity check passed with no measurable probability mismatch.

## Browser parity evidence

Verified parity test:

- 10 valid URLs
- 6 invalid URLs
- max feature delta: 8.88e-16
- max probability delta: 0.0
- result: passed

This confirms that browser inference remains consistent with the Python implementation for the tested cases.

## Verification status

The repository was re-verified with the project’s test command:

```bash
cd /workspaces/safeweb && npm test
```

Result:

```text
48 passed in 12.83s
```

## Limitations

The project remains a prototype and should not be treated as a calibrated real-world detector. It is limited by the available labeled data, the static URL-only feature design, and the absence of an external production validation source.

This means the observed metrics are informative for the project’s internal evaluation and browser parity checks, but they do not claim general real-world phishing detection beyond the dataset used.

## Conclusion

The final project state is stable and validated: the PhishVN-compatible dataset was integrated safely, the Random Forest model was retained as the active performer, the browser export was regenerated and matched, and the repository test suite passed. The final documentation should therefore reflect the 5,000-row dataset and the Random Forest benchmark rather than the earlier synthetic template values.
