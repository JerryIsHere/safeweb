# SafeWeb Poster Content

## Title

SafeWeb: A URL-Feature Research Prototype for Phishing Classification

## Problem

Phishing URLs can imitate familiar services. This project examines whether measurable URL-string patterns can help a classifier distinguish labeled examples.

## Research Question

How well can a Random Forest distinguish the labels in a documented URL dataset using URL-string features alone?

## Hypothesis

A Random Forest may learn patterns associated with phishing in the training data, but it will make errors and cannot prove that a URL is safe or malicious.

## Method

Validate and deduplicate a documented `url,label` dataset, extract deterministic numeric URL features, train a 200-tree Random Forest on a stratified 80% training split, then evaluate on the untouched 20% test split.

## Results

- Dataset and provenance: [TODO]
- Accuracy / precision / recall / F1: [EXPERIMENT NOT RUN]
- Confusion matrix: [EXPERIMENT NOT RUN]
- Main false-positive and false-negative patterns: [EXPERIMENT NOT RUN]

## Safety and Limitations

SafeWeb analyzes URL text only and makes no network requests. Its risk level is a model warning based on training data, not proof of safety or maliciousness. A URL-only model cannot inspect the actual website.

## Conclusion

[Complete only after the experiment. Report what the test set supports and what remains uncertain.]