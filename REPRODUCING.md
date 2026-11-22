# Reproduce the Bank Marketing analysis

Run commands from the repository root. Python 3.12 is the verified reference version. Preserve the original CSV bytes: Excel re-saving can change the delimiter or line endings and fail the hash check.

## 1. Prepare Python

```bash
python -m venv .venv
```

Activate the environment:

- macOS/Linux: `source .venv/bin/activate`
- Windows PowerShell: `.venv\Scripts\Activate.ps1`

Then install the verified numerical package versions:

```bash
python -m pip install -r requirements.txt
```

`requirements.txt` pins the numerical packages used for verification. Exact ranking reproduction can depend on the Python version and numerical platform.

## 2. Obtain the source CSV

Download the Bank Marketing data from [UCI](https://archive.ics.uci.edu/dataset/222/bank+marketing). Extract `bank-additional-full.csv` from the bank-additional archive and place it at:

```text
data/bank-additional-full.csv
```

Use the 41,188-row file, not the smaller sample or the distinct 45,211-row bank-full dataset. The source has 21 semicolon-separated columns, including the outcome `y`.

Expected SHA-256:

```text
74adfc578bf77a7ff4bb1ba4a9f8709d9e3c6907342959c2c8416847e0afb4d8
```

## 3. Run the analysis in order

```bash
python scripts/Bank_Marketing_Stage2_Setup.py data/bank-additional-full.csv work/stage2_data
python scripts/Bank_Marketing_Stage2_Benchmarks.py work/stage2_data/validation.csv
python scripts/Bank_Marketing_Stage2_Logistic.py work/stage2_data
python scripts/Bank_Marketing_Stage3_Final.py data/bank-additional-full.csv work/stage2_data
python scripts/Export_Demonstration_Ranking.py work/stage2_data/final_evaluation.json work/stage2_data/Demonstration_Ranked_List.csv
```

Setup writes development and validation CSVs and an intake audit. The benchmark and logistic scripts write validation JSON files. Stage 3 verifies the original source hash and reproduces the validation ranking before writing `final_evaluation.json`. The last command exports the logistic model's historical selection order; the file illustrates the evaluated model and does not recommend deploying it.

## Jupyter alternative

Use a notebook whose working directory is the repository root and a kernel with the same numerical dependencies installed. Run these cells in order:

```python
%run scripts/Bank_Marketing_Stage2_Setup.py data/bank-additional-full.csv work/stage2_data
%run scripts/Bank_Marketing_Stage2_Benchmarks.py work/stage2_data/validation.csv
%run scripts/Bank_Marketing_Stage2_Logistic.py work/stage2_data
%run scripts/Bank_Marketing_Stage3_Final.py data/bank-additional-full.csv work/stage2_data
%run scripts/Export_Demonstration_Ranking.py work/stage2_data/final_evaluation.json work/stage2_data/Demonstration_Ranked_List.csv
```

## Expected output

| Method | Validation | Final |
| --- | ---: | ---: |
| Logistic regression | 283 | 568 |
| Prior-success rule | 222 | 926 |
| Random selection, expected | 182.33 | 507.82 |

Each method has 1,647 selections per evaluation block. `meets_historical_threshold` in the final JSON is `false`.

Original reference artifacts are in `results/`; rerun outputs go to `work/`. Expected random counts are stored at full precision and rounded to two decimal places for presentation. Compare subscriber counts and selected source row IDs when checking reproduction; paths and environment metadata may differ.
