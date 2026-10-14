# SafeWeb v2.1.0 Poster Content

## Research Question

Can a Random Forest distinguish phishing from benign URLs in PhishVN's grouped temporal test set using SafeWeb URL features and the dataset's pre-extracted lexical/host features?

## Dataset and Method

- PhishVN v3.1.0 open URL archive: 53,116 source rows.
- Canonicalization and `www`/apex deduplication: 36,261 retained URLs; 16,855 aliases removed.
- Official grouped partitions have zero registrable-domain overlap.
- Train plus validation: 29,637 rows. Untouched test: 6,624 rows.
- Random Forest: 100 trees, depth limit 16, minimum leaf size 3; 52 features.
- Feature parity checked for 797,742 dataset feature values.

## Test Results

| Accuracy | Precision | Recall | F1 |
| ---: | ---: | ---: | ---: |
| 0.8752 | 0.8231 | 0.8975 | 0.8587 |

Confusion matrix (`benign`, `phishing`): `[[3285, 540], [287, 2512]]`.

## Product Flow

SafeWeb first checks a PhishVN URL/host/signature index, then always evaluates the Random Forest. Optional live checks are consent-gated and can report DNS, embedded redirect destinations, page metadata, and a screenshot preview. The default path remains local-only.

## Interpretation and Limitations

These are dataset-specific results, not proof of production or real-world detection accuracy. Labels, collection period, class balance, and source selection affect results. Database-match results are separate from ML evaluation. Browser CORS and third-party service availability can limit live redirect and metadata checks. HTTPS is a URL scheme indicator, not certificate verification.
