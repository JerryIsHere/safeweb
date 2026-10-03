# SafeWeb Project Report

## Research Status

This document is a research template. The repository does not include a research dataset or trained model. All fields marked with brackets require evidence from an actual, documented experiment.

## Problem and Motivation

Phishing messages can direct people to URLs designed to imitate legitimate services. URL strings contain measurable characteristics that may help a machine-learning model identify patterns associated with phishing. This project explores those characteristics as an educational prototype.

## Objective

Build and evaluate a model that classifies a URL string as legitimate-like (`0`) or phishing-like (`1`) using URL-derived numeric features, then communicate its output as a risk signal rather than a definitive verdict.

## Research Question

How well can a Random Forest classifier distinguish the labels in a documented URL dataset using only URL-string features?

## Hypothesis

The hypothesis is that a Random Forest trained on labeled data will identify some URL patterns associated with phishing. The hypothesis does not predict perfect classification and must be evaluated against held-out data.

## Scope and Safety

SafeWeb analyzes the submitted string only. It does not visit URLs, follow redirects, execute page content, download files, or collect credentials, cookies, or tokens. The model's findings are limited to URL characteristics and its training data.

## Theoretical Background

The feature extractor calculates string lengths, character counts, hostname structure, keyword indicators, IP-host indicators, and Shannon entropy. These features are signals, not proof. HTTPS alone does not establish legitimacy, and a keyword or unusual character pattern alone does not establish phishing.

## Dataset

- Dataset name and source: [DATASET NOT SELECTED]
- Collection date and license: [TODO]
- Number of rows before duplicate removal: [EXPERIMENT NOT RUN]
- Number of rows after duplicate removal: [EXPERIMENT NOT RUN]
- Legitimate / phishing class counts: [EXPERIMENT NOT RUN]
- Inclusion, exclusion, and labeling rules: [TODO]

Do not enter results from development fixtures as research results. Record dataset provenance and any known sampling or labeling limitations.

## Preprocessing and Features

The loader requires `url` and `label` columns, non-empty URLs, and labels in `{0, 1}`. Exact duplicate URLs are removed; conflicting duplicate labels are rejected. A stratified split uses `test_size=0.20` and `random_state=42`. Feature extraction is deterministic and requires no network access.

## Machine-Learning Method

The initial estimator is `RandomForestClassifier(n_estimators=200, random_state=42)`. It is fitted only on the training partition. The test partition is reserved for final evaluation and must not be used for tuning.

## System Architecture

CSV ingestion and validation feed deterministic feature extraction. Training saves a model bundle; prediction loads that bundle and returns a class, phishing probability, configured risk level, extracted features, and cautious signal explanations. The Flask interface sends only URL strings to the local application.

## Experiment Design

1. Record dataset provenance and freeze the labeled CSV used for the experiment.
2. Train on the stratified 80% training partition with the specified seed and estimator settings.
3. Evaluate once on the held-out 20% test partition.
4. Record the software versions, data-cleaning decisions, metrics, confusion matrix, and error examples.
5. Do not tune on the test partition. If tuning is needed, use a separate validation or cross-validation procedure and retain a final untouched test set.

## Evaluation Results

- Accuracy: [EXPERIMENT NOT RUN]
- Precision: [EXPERIMENT NOT RUN]
- Recall: [EXPERIMENT NOT RUN]
- F1-score: [EXPERIMENT NOT RUN]
- Confusion matrix: [EXPERIMENT NOT RUN]
- Classification report: [EXPERIMENT NOT RUN]

No performance values are reported until the experiment is run on a documented research dataset.

## Error Analysis

- True positives: [EXPERIMENT NOT RUN]
- True negatives: [EXPERIMENT NOT RUN]
- False positives: [EXPERIMENT NOT RUN]
- False negatives: [EXPERIMENT NOT RUN]
- Error patterns and interpretation: [TODO AFTER EVALUATION]

## Limitations

The model can reproduce dataset bias, fail on new URL patterns, or be affected by mislabeled and stale records. URL-only analysis cannot inspect site behavior, certificates, page content, or reputation. Model probabilities are not guarantees and should not be interpreted as calibrated certainty without a separate calibration study.

## Future Work

Possible follow-up work includes collecting a better documented dataset, evaluating temporal and source-based generalization, comparing baselines under the same split protocol, checking probability calibration, and improving error analysis. Any added data source or network feature needs a separate safety and privacy review.

## Conclusion

[WRITE AFTER THE EXPERIMENT. Distinguish the measured result from the original hypothesis and state limitations.]