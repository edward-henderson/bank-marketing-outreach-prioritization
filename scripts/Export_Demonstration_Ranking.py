"""Export the historical demonstration ranking from a Stage 3 results JSON."""

import argparse
import csv
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results_json", type=Path)
    parser.add_argument("output_csv", type=Path)
    args = parser.parse_args()
    results = json.loads(args.results_json.read_text(encoding="utf-8"))
    row_ids = results["logistic_selected_source_row_ids"]
    with args.output_csv.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["demonstration_rank", "historical_source_row_id", "use"])
        writer.writerows(
            (rank, row_id, "historical demonstration only")
            for rank, row_id in enumerate(row_ids, start=1)
        )


if __name__ == "__main__":
    main()
