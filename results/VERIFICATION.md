# Reproduction verification

The packaged scripts were rerun sequentially against the unmodified source CSV using Python 3.12.14, scikit-learn 1.8.0, NumPy 2.3.5, and SciPy 1.17.0.

The validation benchmark JSON, validation model comparison JSON, and final evaluation JSON matched the reference JSON contents exactly. The demonstration ranking CSV matched the reference bytes exactly.

Validation subscriber counts: logistic 283; prior-success rule 222; random expected 182.33.

Final subscriber counts: logistic 568; prior-success rule 926; random expected 507.82.

Final historical threshold met: false.
