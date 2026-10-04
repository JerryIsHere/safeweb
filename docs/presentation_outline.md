# SafeWeb Presentation Outline

1. **Problem and motivation**: Explain phishing URLs and why URL-string signals are worth studying.
2. **Research question and hypothesis**: Present the question and a testable, non-absolute hypothesis.
3. **Scope and safety**: Demonstrate that SafeWeb analyzes text only and does not visit submitted websites.
4. **Dataset**: Give the source, license, labeling process, cleaning decisions, and class counts. Use `[TODO]` until established.
5. **Feature engineering**: Show examples of length, hostname, character, keyword, and entropy features; emphasize they are not proof.
6. **Model and experiment**: Describe the Random Forest parameters and the stratified 80/20 split with the test set held out.
7. **Results and error analysis**: Present measured accuracy, precision, recall, F1, confusion matrix, false positives, and false negatives. Use `[EXPERIMENT NOT RUN]` until measured.
8. **Limitations and conclusion**: Discuss dataset bias, unseen URLs, URL-only scope, and what the experiment does and does not support.