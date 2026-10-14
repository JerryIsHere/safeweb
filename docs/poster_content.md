# SafeWeb v2.3.0 Poster Content

## Research Question

How do four URL classifiers compare on PhishVN's domain-disjoint test set using SafeWeb URL features and the dataset's pre-extracted lexical/host features?

## Dataset and Method

- PhishVN v3.1.0 open URL archive: 53,116 source rows.
- Canonicalization and `www`/apex deduplication: 36,261 retained URLs; 16,855 aliases removed.
- Official grouped partitions have zero registrable-domain overlap.
- Train plus validation: 29,637 rows. Untouched test: 6,624 rows.
- Four classifiers share the same 52 features and domain-disjoint split: Random Forest, Gradient Boosting, calibrated linear SVM, and Logistic Regression.
- Feature parity checked for 797,742 dataset feature values.

## Test Results

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
| --- | ---: | ---: | ---: | ---: | ---: |
| Random Forest | 0.8752 | 0.8231 | 0.8975 | 0.8587 | 0.9466 |
| Gradient Boosting | 0.8798 | 0.8008 | 0.9525 | 0.8701 | 0.9495 |
| Calibrated SVM | 0.8798 | 0.8054 | 0.9436 | 0.8690 | 0.9456 |
| Logistic Regression | 0.8631 | 0.8326 | 0.8460 | 0.8393 | 0.9440 |

Confusion matrix (`benign`, `phishing`): `[[3285, 540], [287, 2512]]`.

## Product Flow

SafeWeb checks the PhishVN URL/host/signature index and evaluates all four models, showing source metadata and model scores separately. Optional live checks are consent-gated; database exploration and local inference need no network services.

## Interpretation and Limitations

These are dataset-specific results, not proof of production or real-world detection accuracy. Labels, collection period, class balance, and source selection affect results. Database-match results are separate from ML evaluation. Browser CORS and third-party service availability can limit live redirect and metadata checks. HTTPS is a URL scheme indicator, not certificate verification.
