# SafeWeb v2.1.0 Presentation Outline

1. **Problem**: Why phishing URLs can imitate familiar services and why URL evidence is only one signal.
2. **Research question**: Evaluate a Random Forest on PhishVN's grouped temporal test set.
3. **Dataset**: 53,116 source rows; timestamps, label provenance, official train/validation/test groups, and 21 pre-extracted CompPhish features.
4. **Cleaning**: Canonical URL identity, 16,855 `www`/apex aliases removed, 36,261 retained records, no observed conflicting labels or inter-partition registrable-domain overlap.
5. **Features and model**: 52 features; 100-tree Random Forest with depth 16 and minimum leaf size 3; trained on train plus validation.
6. **Results**: Accuracy 0.8752, phishing precision 0.8231, recall 0.8975, F1 0.8587 on 6,624 untouched test rows; show the confusion matrix and discuss false positives/negatives.
7. **Two-stage product**: PhishVN lookup provenance followed by ML, then optional DNS/redirect/metadata/screenshot inspection after explicit consent.
8. **Safety and limitations**: Local-only default, external providers receive URL only after opt-in, CORS may hide redirects, HTTPS scheme is not certificate validation, metrics are dataset-specific.
9. **Deployment and verification**: Python/browser parity, automated tests, static build, and main-only GitHub Pages workflow.
