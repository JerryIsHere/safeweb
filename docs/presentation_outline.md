# SafeWeb v2.3.0 Presentation Outline

1. **Problem**: Why phishing URLs can imitate familiar services and why URL evidence is only one signal.
2. **Research question**: Compare four URL classifiers trained on PhishVN + PhiUSIIL against PhishVN's untouched domain-disjoint test set.
3. **Dataset**: 53,116 source rows; timestamps, label provenance, official train/validation/test groups, and 21 pre-extracted CompPhish features.
4. **Cleaning**: Canonical URL identity, 16,855 `www`/apex aliases removed, 36,261 retained records, no observed conflicting labels or inter-partition registrable-domain overlap.
5. **Features and models**: Shared 55 URL-only features; 29,637 PhishVN + 231,662 cleaned PhiUSIIL fit rows, equal-weighted by source; RF, GB, calibrated linear SVM, and scaled Logistic Regression.
6. **Results**: On the same 6,624 untouched PhishVN rows, accuracy is 0.8745/0.8789/0.5805/0.8555 and ROC-AUC is 0.9426/0.9436/0.9308/0.9330; flag the SVM's 0.0071 phishing recall.
7. **Two-stage product**: PhishVN lookup provenance followed by ML, then optional DNS/redirect/metadata/screenshot inspection after explicit consent.
8. **Safety and limitations**: Local-only default, external providers receive URL only after opt-in, CORS may hide redirects, HTTPS scheme is not certificate validation, metrics are dataset-specific.
9. **Deployment and verification**: Python/browser parity, automated tests, static build, and main-only GitHub Pages workflow.
