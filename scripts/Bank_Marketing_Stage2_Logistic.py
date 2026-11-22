"""Fit the BANK-001 logistic candidate and compare it on validation.

Jupyter: %run Bank_Marketing_Stage2_Logistic.py stage2_data
Keep the setup and benchmark scripts beside this script. Requires scikit-learn.
Writes validation_logistic_comparison.json in the prepared data folder.
"""

import argparse
import csv
import json
import random
from pathlib import Path

import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from Bank_Marketing_Stage2_Benchmarks import (
    SELECTION_COUNT, metrics, prior_success_selection, read_validation,
)
from Bank_Marketing_Stage2_Setup import BLOCKS, OUTPUT_COLUMNS, PREDICTORS, TARGET

NUMERIC = ("age", "previous")
CATEGORICAL = tuple(field for field in PREDICTORS if field not in NUMERIC)
TIE_SEED = 42


def read_development(path):
    _, first, last, expected_yes = BLOCKS[0]
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not set(OUTPUT_COLUMNS).issubset(reader.fieldnames or []):
            raise ValueError("Use development.csv from the Stage 2 setup script.")
        rows = list(reader)

    if [int(row["source_row_id"]) for row in rows] != list(range(first, last + 1)):
        raise ValueError("Expected the approved development records in source order.")
    if any(row[TARGET] not in ("yes", "no") for row in rows):
        raise ValueError("Unexpected development outcome.")
    if sum(row[TARGET] == "yes" for row in rows) != expected_yes:
        raise ValueError("Development subscriber count differs from the approved intake count.")
    return rows


def feature_matrix(rows):
    return [
        [float(row[field]) for field in NUMERIC] + [row[field] for field in CATEGORICAL]
        for row in rows
    ]


def compare(folder):
    development = read_development(folder / "development.csv")
    validation = read_validation(folder / "validation.csv")
    total_subscribers = sum(row[TARGET] == "yes" for row in validation)
    if total_subscribers != BLOCKS[1][3]:
        raise ValueError("Validation subscriber count differs from the approved intake count.")

    first_categorical = len(NUMERIC)
    preprocessing = ColumnTransformer([
        ("numeric", StandardScaler(), list(range(first_categorical))),
        ("categorical", OneHotEncoder(handle_unknown="ignore"),
         list(range(first_categorical, first_categorical + len(CATEGORICAL)))),
    ])
    model = make_pipeline(
        preprocessing,
        LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000),
    )
    model.fit(feature_matrix(development), [row[TARGET] == "yes" for row in development])
    scores = model.predict_proba(feature_matrix(validation))[:, 1]

    # Pre-shuffle with a fixed seed so exact score ties do not favor source order.
    ranked = list(zip(scores, validation))
    random.Random(TIE_SEED).shuffle(ranked)
    ranked.sort(key=lambda pair: pair[0], reverse=True)
    selected = [row for _, row in ranked[:SELECTION_COUNT]]
    prior = prior_success_selection(validation, SELECTION_COUNT)

    logistic_subscribers = sum(row[TARGET] == "yes" for row in selected)
    prior_subscribers = sum(row[TARGET] == "yes" for row in prior)
    random_expected = SELECTION_COUNT * total_subscribers / len(validation)
    comparison = {
        "random_selection_expected": metrics(random_expected, SELECTION_COUNT, total_subscribers),
        "prior_campaign_success_observed": metrics(prior_subscribers, SELECTION_COUNT, total_subscribers),
        "logistic_regression_observed": metrics(logistic_subscribers, SELECTION_COUNT, total_subscribers),
    }
    result = {
        "development_records": len(development),
        "validation_records": len(validation),
        "validation_subscribers": total_subscribers,
        "model": {
            "numeric_standardized": list(NUMERIC),
            "categorical_one_hot": list(CATEGORICAL),
            "unseen_categories": "Ignored by the fitted encoder",
            "solver": "lbfgs",
            "regularization": "L2, C=1.0",
            "class_weight": None,
            "max_iter": 1000,
            "sklearn_version": sklearn.__version__,
            "exact_score_tie_seed": TIE_SEED,
        },
        "comparison": comparison,
        "logistic_subscribers_above_expected_random": logistic_subscribers - random_expected,
        "logistic_subscribers_above_prior_success": logistic_subscribers - prior_subscribers,
        "logistic_selected_source_row_ids": [int(row["source_row_id"]) for row in selected],
    }
    path = folder / "validation_logistic_comparison.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for name, row in comparison.items():
        print(
            f"{name}: {row['subscribers']:.2f} subscribers, "
            f"{row['selected_subscription_rate']:.2%} selected subscription rate, "
            f"{row['subscriber_capture_rate']:.2%} subscriber capture"
        )
    print(f"Saved {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_folder", type=Path)
    compare(parser.parse_args().data_folder)
