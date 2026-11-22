"""Prepare BANK-001 development and validation data from the original source CSV.

Run: python Bank_Marketing_Stage2_Setup.py bank-additional-full.csv stage2_data

The script assigns 1-based source row IDs before filtering and writes two
modeling CSVs and a JSON audit. The final block is checked for intake counts
and stays in the source file for Stage 3. No external packages are required.
"""

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

CLIENT_FIELDS = ("age", "job", "marital", "education", "default", "housing", "loan")
HISTORY_FIELDS = ("previous", "poutcome")
PREDICTORS = CLIENT_FIELDS + HISTORY_FIELDS
EXCLUDED = ("duration", "campaign")
HELD = (
    "contact", "month", "day_of_week", "pdays", "emp.var.rate",
    "cons.price.idx", "cons.conf.idx", "euribor3m", "nr.employed",
)
TARGET = "y"
# Inclusive source row boundaries, excluding the header.
BLOCKS = (
    ("development", 1, 24712, 1188),
    ("validation", 24713, 32950, 912),
    ("final_evaluation", 32951, 41188, 2540),
)
OUTPUT_COLUMNS = ("source_row_id", *PREDICTORS, TARGET)


def prepare(source, output_dir):
    """Validate the source and write reproducible Stage 2 inputs."""
    fields = {*PREDICTORS, *EXCLUDED, *HELD, TARGET}
    prepared = {"development": [], "validation": []}
    summary = {}
    seen = set()
    duplicate_rows = 0

    with source.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter=";")
        if len(reader.fieldnames or []) != len(fields) or set(reader.fieldnames or []) != fields:
            raise ValueError("Expected the 21 fields of bank-additional-full.csv.")

        for name, first, last, expected_yes in BLOCKS:
            outcomes = Counter()
            for row_id in range(first, last + 1):
                row = next(reader, None)
                if row is None:
                    raise ValueError(f"Source ended before record {row_id}.")
                if None in row or any(value in (None, "") for value in row.values()):
                    raise ValueError(f"Wrong field count or blank value at record {row_id}.")
                if row[TARGET] not in ("yes", "no"):
                    raise ValueError(f"Unexpected outcome at record {row_id}.")

                raw_values = tuple(row.values())
                duplicate_rows += raw_values in seen
                seen.add(raw_values)
                outcomes[row[TARGET]] += 1
                if name in prepared:
                    prepared[name].append((row_id, *(row[field] for field in OUTPUT_COLUMNS[1:])))

            if outcomes["yes"] != expected_yes:
                raise ValueError(f"{name} outcome count differs from the approved intake counts.")
            size = last - first + 1
            summary[name] = {
                "first_source_row_id": first,
                "last_source_row_id": last,
                "records": size,
                "subscriptions": outcomes["yes"],
                "subscription_rate": outcomes["yes"] / size,
            }

        if next(reader, None) is not None:
            raise ValueError("Source contains more than 41,188 records.")

    output_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in prepared.items():
        with (output_dir / f"{name}.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(OUTPUT_COLUMNS)
            writer.writerows(rows)

    audit = {
        "source": source.name,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "blocks": summary,
        "exact_repeated_rows_retained": duplicate_rows,
        "candidate_predictors": list(PREDICTORS),
        "predictor_assumptions": {
            "client_fields": "Treat recorded client attributes as available when the list was prepared.",
            "history_fields": "Previous contact count and outcome refer to completed prior campaigns.",
            "unknown": "Preserved as an explicit category.",
        },
        "excluded_current_outreach_fields": list(EXCLUDED),
        "held_pending_timing_confirmation": list(HELD),
        "outcome": TARGET,
        "row_id": "Source position excluding header. Identifier only.",
        "stage_2_selection_count": 1647,
        "stage_3_selection_count": 1647,
        "final_block_handling": "Intake counts checked. Rows remain in source and are not exported for Stage 2.",
    }
    audit_path = output_dir / "setup_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    return audit_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    print(prepare(args.source, args.output_dir))
