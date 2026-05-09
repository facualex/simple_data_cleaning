import logging
from pathlib import Path

import pandas as pd

from cleaning import clean
from logging_config import configure_logging
from profiling import profile

configure_logging()

logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).parent.parent / "data" / "raw" / "dirty_cafe_sales.csv"

raw_df = pd.read_csv(DATA_PATH)


def pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """Profile the raw data, clean it, then profile the result for comparison."""
    logger.info("Pipeline started...")

    profile(df, out_filename="first_profile.html")

    clean_df = clean(df)

    profile(clean_df, out_filename="clean_profile.html")

    logger.info("Pipelined finished succesfully.")


pipeline(raw_df)
