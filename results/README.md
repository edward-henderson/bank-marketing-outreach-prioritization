# Reference results

These files preserve the original analysis run:

| File | Contents |
| --- | --- |
| `setup_audit.json` | Intake counts, split definitions, and feature availability assumptions |
| `validation_benchmarks.json` | Random expectation and prior-success validation selections |
| `validation_logistic_comparison.json` | Fitted model configuration and validation ranking |
| `Bank_Marketing_Stage3_Results.json` | Final comparison; reruns name this `final_evaluation.json` |
| `Demonstration_Ranked_List.csv` | Logistic model's 1,647 final selections in rank order |

The CSV identifies historical source positions, not bank customer IDs. It is a demonstration of the evaluated logistic ranking, whose live pilot was deferred.

- `selections`: number of historical records selected.
- `subscribers`: selected records whose current outcome `y` is `yes`; fractional for random expectation.
- `selected_subscription_rate`: subscribers divided by selections.
- `subscriber_capture_rate`: selected subscribers divided by all subscribers in that block.

These measures describe historical subscriber capture. They do not measure incremental deposits, causal effects, or deposits per outbound attempt.
