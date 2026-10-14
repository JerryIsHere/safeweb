# SafeWeb v2.3.0 Poster Content

## Research Question

How do four URL classifiers trained on PhishVN plus PhiUSIIL compare on the untouched PhishVN domain-disjoint test set?

## Dataset and Method

- PhishVN v3.1.0 open URL archive: 53,116 source rows.
- Canonicalization and `www`/apex deduplication: 36,261 retained URLs; 16,855 aliases removed.
- Official grouped partitions have zero registrable-domain overlap.
- Train plus validation: 29,637 rows. Untouched test: 6,624 rows.
- Added 231,662 cleaned PhiUSIIL fit rows; removed 86 conflicting labels, 3,586 duplicate URLs, and 461 PhishVN test-domain overlaps.
- Four classifiers share 55 URL-only features; sources receive equal total fit weight.
- Feature parity checked for 797,742 dataset feature values.

## Test Results

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
| --- | ---: | ---: | ---: | ---: | ---: |
| Random Forest | 0.8745 | 0.8075 | 0.9232 | 0.8615 | 0.9426 |
| Gradient Boosting | 0.8789 | 0.7976 | 0.9561 | 0.8697 | 0.9436 |
| Calibrated SVM | 0.5805 | 1.0000 | 0.0071 | 0.0142 | 0.9308 |
| Logistic Regression | 0.8555 | 0.7996 | 0.8782 | 0.8371 | 0.9330 |

Confusion matrices (`benign`, `phishing`): RF `[[3209,616],[215,2584]]`; GB `[[3146,679],[123,2676]]`; SVM `[[3825,0],[2779,20]]`; LR `[[3209,616],[341,2458]]`. The SVM's current threshold has unusably low phishing recall and needs recalibration.

## Product Flow

SafeWeb checks the PhishVN URL/host/signature index and evaluates all four models, showing source metadata and model scores separately. Optional live checks are consent-gated; database exploration and local inference need no network services.

## Interpretation and Limitations

These are dataset-specific results, not proof of production or real-world detection accuracy. Labels, collection period, class balance, and source selection affect results. Database-match results are separate from ML evaluation. Browser CORS and third-party service availability can limit live redirect and metadata checks. HTTPS is a URL scheme indicator, not certificate verification.
