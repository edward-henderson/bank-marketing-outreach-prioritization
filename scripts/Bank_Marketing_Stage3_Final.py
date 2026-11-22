"""Evaluate the frozen BANK-001 candidate on the reserved final records.

Jupyter: %run Bank_Marketing_Stage3_Final.py bank-additional-full.csv stage2_data
Keep the three Stage 2 scripts in the same folder as this script. Run the
Stage 2 setup and logistic comparison first. Requires scikit-learn.
Writes final_evaluation.json in the prepared data folder.
"""

import argparse
import csv
import hashlib
import json
import random
from itertools import islice
from pathlib import Path

import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from Bank_Marketing_Stage2_Benchmarks import (
    PRIOR_SUCCESS_SEED,
    SELECTION_COUNT,
    metrics,
    prior_success_selection,
    read_validation,
)
from Bank_Marketing_Stage2_Logistic import (
    CATEGORICAL,
    NUMERIC,
    TIE_SEED,
    feature_matrix,
    read_development,
)
from Bank_Marketing_Stage2_Setup import BLOCKS, TARGET

SOURCE_SHA256 = "74adfc578bf77a7ff4bb1ba4a9f8709d9e3c6907342959c2c8416847e0afb4d8"
MIN_SUBSCRIBER_GAIN = 33


def fit_frozen_candidate(development):
    preprocessing = ColumnTransformer([
        ("numeric", StandardScaler(), list(range(len(NUMERIC)))),
        ("categorical", OneHotEncoder(handle_unknown="ignore"),
         list(range(len(NUMERIC), len(NUMERIC) + len(CATEGORICAL)))),
    ])
    model = make_pipeline(
        preprocessing,
        LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000),
    )
    return model.fit(feature_matrix(development), [row[TARGET] == "yes" for row in development])


def select_by_score(model, rows):
    scores = model.predict_proba(feature_matrix(rows))[:, 1]
    ranked = list(zip(scores, rows))
    random.Random(TIE_SEED).shuffle(ranked)
    ranked.sort(key=lambda pair: pair[0], reverse=True)
    return [row for _, row in ranked[:SELECTION_COUNT]]


def source_ids(rows):
    return [int(row["source_row_id"]) for row in rows]


def evaluate(source, folder):
    development = read_development(folder / "development.csv")
    validation = read_validation(folder / "validation.csv")
    validation_report = json.loads((folder / "validation_logistic_comparison.json").read_text())

    # Verify the locked candidate reproduces the Stage 2 selections before
    # comparing against final outcomes. The fitted model uses development only.
    model = fit_frozen_candidate(development)
    if source_ids(select_by_score(model, validation)) != validation_report["logistic_selected_source_row_ids"]:
        raise ValueError("The frozen candidate did not reproduce the Stage 2 validation ranking.")

    if hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("Use the original source CSV verified in Stage 2.")
    _, first, last, expected_yes = BLOCKS[2]
    with source.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter=";")
        final_rows = [
            {"source_row_id": row_id, **row}
            for row_id, row in enumerate(islice(reader, first - 1, last), start=first)
        ]

    ranked = select_by_score(model, final_rows)
    prior = prior_success_selection(final_rows, SELECTION_COUNT)
    total_subscribers = sum(row[TARGET] == "yes" for row in final_rows)
    if len(final_rows) != last - first + 1 or total_subscribers != expected_yes:
        raise ValueError("Final block differs from the approved intake counts.")

    model_yes = sum(row[TARGET] == "yes" for row in ranked)
    prior_yes = sum(row[TARGET] == "yes" for row in prior)
    expected_random_yes = SELECTION_COUNT * total_subscribers / len(final_rows)
    gains = {
        "above_random_expected": model_yes - expected_random_yes,
        "above_prior_campaign_success": model_yes - prior_yes,
    }
    result = {
        "block": "final_evaluation",
        "source_sha256": SOURCE_SHA256,
        "source_row_ids_inclusive": [first, last],
        "records": len(final_rows),
        "subscribers": total_subscribers,
        "model": validation_report["model"],
        "scoring_sklearn_version": sklearn.__version__,
        "development_records": len(development),
        "stage2_validation_ranking_reproduced": True,
        "comparison": {
            "random_selection_expected": metrics(expected_random_yes, SELECTION_COUNT, total_subscribers),
            "prior_campaign_success_observed": metrics(prior_yes, len(prior), total_subscribers),
            "logistic_regression_observed": metrics(model_yes, len(ranked), total_subscribers),
        },
        "prior_success_seed": PRIOR_SUCCESS_SEED,
        "prior_success_records_selected": sum(row["poutcome"] == "success" for row in prior),
        "gains_in_subscribers": gains,
        "minimum_gain_against_each_benchmark": MIN_SUBSCRIBER_GAIN,
        "meets_historical_threshold": min(gains.values()) >= MIN_SUBSCRIBER_GAIN,
        "logistic_selected_source_row_ids": source_ids(ranked),
        "prior_success_selected_source_row_ids": source_ids(prior),
    }
    output = folder / "final_evaluation.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for name, row in result["comparison"].items():
        print(f"{name}: {row['subscribers']:.2f} subscribers, "
              f"{row['selected_subscription_rate']:.2%} selected subscription rate, "
              f"{row['subscriber_capture_rate']:.2%} subscriber capture")
    print(f"Meets historical threshold: {result['meets_historical_threshold']}")
    print(f"Saved {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_csv", type=Path)
    parser.add_argument("stage2_folder", type=Path)
    args = parser.parse_args()
    evaluate(args.source_csv, args.stage2_folder)
