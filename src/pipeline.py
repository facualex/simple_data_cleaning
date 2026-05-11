import json
import logging
from pathlib import Path

import pandas as pd

from cleaning import clean
from logging_config import configure_logging
from profiling import profile

logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).parent.parent / "data" / "raw" / "dirty_cafe_sales.csv"


def pipeline(df: pd.DataFrame, log_path: Path) -> pd.DataFrame:
    """Profile the raw data, clean it, then profile the result for comparison."""
    logger.info("Pipeline started...")

    profile(df, out_filename="first_profile.html")

    clean_df, cleaning_report = clean(df)

    profile(clean_df, out_filename="clean_profile.html")

    report_path = log_path.with_suffix(".json")

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(cleaning_report, f, indent=2, default=str)

    logger.info("Cleaning report written to %s.", report_path)
    logger.info("Pipelined finished succesfully.")


if __name__ == "__main__":
    log_path = configure_logging()

    raw_df = pd.read_csv(DATA_PATH)

    pipeline(raw_df, log_path)
