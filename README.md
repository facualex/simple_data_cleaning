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

Each step is a composable `DataFrame → (DataFrame, summary)` transformation. The summaries are aggregated into a JSON cleaning report written at the end of every run.

```
raw CSV
  → map_sentinels_to_null    replace "ERROR" / "UNKNOWN" with pd.NA
  → type_casting             cast Quantity (Int64), prices (float64), dates (datetime64)
  → derive_total_spent       recompute Total Spent = Quantity × Price Per Unit where possible
  → remove_nulls_from_critical_fields   drop rows still missing Item, Quantity, Price Per Unit, or Total Spent
  → clean DataFrame + cleaning report (JSON)
```

Before and after the cleaning step, the pipeline generates a [sweetviz](https://github.com/fbdesignpro/sweetviz) HTML report so the impact of each decision is visible and reproducible.

---

## Outputs

Every run produces four artifacts:

| Path | Description |
|---|---|
| `logs/YYYYMMDD/<timestamp>.log` | Structured run log (console-mirrored) |
| `logs/YYYYMMDD/<timestamp>.json` | Cleaning report — row counts, per-step summaries, `generated_at` timestamp |
| `reports/first_profile.html` | sweetviz EDA of the raw input |
| `reports/clean_profile.html` | sweetviz EDA after cleaning |

---

## Project Structure

```
.
├── data/
│   ├── raw/                  # Source data (not tracked by git)
│   └── processed/            # Output data (not tracked by git)
├── logs/                     # Date-organized run logs and cleaning reports
│   └── YYYYMMDD/
│       ├── HHMMss-<microseconds>.log
│       └── HHMMss-<microseconds>.json
├── reports/                  # sweetviz HTML reports (before/after cleaning)
├── src/
│   ├── pipeline.py           # Entry point — orchestrates profiling, cleaning, and reporting
│   ├── cleaning.py           # Cleaning steps as pure (DataFrame, summary) transformations
│   ├── profiling.py          # sweetviz report generation
│   └── logging_config.py     # Structured logging setup (console + file handlers)
├── tests/
│   └── test_cleaning.py
└── requirements.txt
```

---

## Running It

**1. Add the raw dataset**

Place `dirty_cafe_sales.csv` in `data/raw/`.

**2. Build the image**

```bash
docker build -t cafe-pipeline .
```

**3. Run the pipeline**

```bash
docker run -v $(pwd)/data:/app/data cafe-pipeline
```

> The raw dataset is not included in the image — the volume mount makes your local `data/raw/` available inside the container. Outputs are written back to your local `data/processed/`.

To override the log level:

```bash
docker run -e LOG_LEVEL=DEBUG -v $(pwd)/data:/app/data cafe-pipeline
```

**4. Run tests**

```bash
docker run --entrypoint pytest cafe-pipeline
```

---

## Tech Stack

| Tool | Role |
|---|---|
| [pandas](https://pandas.pydata.org/) | Data transformation |
| [sweetviz](https://github.com/fbdesignpro/sweetviz) | Automated EDA reports |
| [pytest](https://pytest.org/) | Unit testing |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Environment configuration |
