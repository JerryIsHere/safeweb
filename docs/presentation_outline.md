# SafeWeb v2.3.0 Presentation Outline

1. **Problem**: Why phishing URLs can imitate familiar services and why URL evidence is only one signal.
2. **Research question**: Compare four classifiers on PhishVN's domain-disjoint test set.
3. **Dataset**: 53,116 source rows; timestamps, label provenance, official train/validation/test groups, and 21 pre-extracted CompPhish features.
4. **Cleaning**: Canonical URL identity, 16,855 `www`/apex aliases removed, 36,261 retained records, no observed conflicting labels or inter-partition registrable-domain overlap.
5. **Features and models**: Shared 52-feature schema; Random Forest, Gradient Boosting, calibrated linear SVM, and scaled Logistic Regression; 29,637 training rows.
6. **Results**: On the same 6,624 untouched rows, accuracy is 0.8752/0.8798/0.8798/0.8631 and ROC-AUC is 0.9466/0.9495/0.9456/0.9440 respectively; compare all confusion matrices and class trade-offs.
7. **Two-stage product**: PhishVN lookup provenance followed by ML, then optional DNS/redirect/metadata/screenshot inspection after explicit consent.
8. **Safety and limitations**: Local-only default, external providers receive URL only after opt-in, CORS may hide redirects, HTTPS scheme is not certificate validation, metrics are dataset-specific.
9. **Deployment and verification**: Python/browser parity, automated tests, static build, and main-only GitHub Pages workflow.
