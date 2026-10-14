# SafeWeb v2.1.0 Implementation Record

## Completed

- Integrated the nested PhishVN v3.1.0 open archive and its official grouped temporal partitions.
- Added canonical URL normalization, `www`/apex deduplication, conflicting-label removal, timestamp retention, and split-overlap checks.
- Added and parity-checked the 21 pre-extracted CompPhish features plus a source-derived suspicious-TLD flag.
- Trained a 100-tree, depth-limited Random Forest on train plus validation; evaluated on the untouched test set.
- Exported model trees, public suffix rules, phishing URL/host references, feature signatures, and compact host profiles for the browser.
- Added URL auto-healing, PhishVN database matching, ML verification, local-first behavior, explicit live-inspection consent, qualitative risk meter, localization, theme controls, and results panels.
- Configured GitHub Pages deployment to build and deploy from `main`.

## Verified Dataset and Metrics

- 53,116 archive rows; 36,261 retained; 16,855 duplicate aliases removed.
- Split counts: train 25,185; validation 4,452; test 6,624; zero registrable-domain overlap.
- Model test accuracy 0.8752; phishing precision 0.8231; recall 0.8975; F1 0.8587.
- Feature parity: 797,742 values compared, no mismatches on the cleaned dataset.

## Remaining Product Limits

- Direct HTTP redirect-chain inspection is restricted by browser CORS; embedded redirect parameters are handled and Microlink may reveal a resolved URL.
- DNS, metadata, and screenshots depend on external providers and are deliberately opt-in.
- HTTPS status reflects the submitted URL's scheme and does not verify the destination's TLS certificate.
- Results are research signals and are not calibrated guarantees of real-world detection.
