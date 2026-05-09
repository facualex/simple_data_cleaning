# Café Sales Data Cleaning Pipeline

A data engineering project that takes a deliberately dirty 10,000-row café sales dataset and produces a clean, analysis-ready version through a structured pandas pipeline. The focus is on realistic data quality problems: sentinel placeholders, wrong column types, missing values that can be recovered, and rows that must be dropped.

---

## The Problem

The raw dataset (`dirty_cafe_sales.csv`) simulates the kind of data quality issues common in transactional systems:

| Issue | Example |
|---|---|
| Sentinel placeholders instead of nulls | `"ERROR"`, `"UNKNOWN"` in numeric and categorical fields |
| Columns stored as the wrong type | `Quantity` and prices stored as strings |
| Recoverable missing values | `Total Spent` is null but `Quantity` and `Price Per Unit` are both present |
| Unrecoverable missing values | Rows where critical fields cannot be filled |

---

## Pipeline

The cleaning pipeline (`src/cleaning.py`) is built as a chain of composable `DataFrame → DataFrame` steps:

```
raw CSV
  → map_sentinels_to_null    replace "ERROR" / "UNKNOWN" with pd.NA
  → type_casting             cast Quantity (Int64), prices (float64), dates (datetime64)
  → derive_total_spent       recompute Total Spent = Quantity × Price Per Unit where possible
  → remove_nulls_from_critical_fields   drop rows still missing Item, Quantity, Price Per Unit, or Total Spent
  → clean DataFrame
```

Before and after the cleaning step, the pipeline generates a [sweetviz](https://github.com/fbdesignpro/sweetviz) HTML report so the impact of each decision is visible and reproducible.

---

## Project Structure

```
.
├── data/
│   ├── raw/                  # Source data (not tracked by git)
│   └── processed/            # Output data (not tracked by git)
├── logs/                     # Timestamped run logs, one file per execution
├── reports/                  # sweetviz HTML reports (before/after cleaning)
├── src/
│   ├── pipeline.py           # Entry point — orchestrates profiling and cleaning
│   ├── cleaning.py           # Cleaning steps as pure DataFrame transformations
│   ├── profiling.py          # sweetviz report generation
│   └── logging_config.py     # Structured logging setup (console + file handlers)
├── tests/
│   └── test_cleaning.py
└── requirements.txt
```

---

## Running It

**1. Install dependencies**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Add the raw dataset**

Place `dirty_cafe_sales.csv` in `data/raw/`.

**3. Run the pipeline**

```bash
python src/pipeline.py
```

The cleaned data is logged, and two HTML reports are written to `reports/`:
- `first_profile.html` — profile of the raw input
- `clean_profile.html` — profile after cleaning

**4. Run tests**

```bash
pytest
```

---

## Tech Stack

| Tool | Role |
|---|---|
| [pandas](https://pandas.pydata.org/) | Data transformation |
| [sweetviz](https://github.com/fbdesignpro/sweetviz) | Automated EDA reports |
| [pandera](https://pandera.readthedocs.io/) | Schema validation |
| [pytest](https://pytest.org/) | Unit testing |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Environment configuration |
