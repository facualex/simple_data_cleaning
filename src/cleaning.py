import logging
from typing import List

import pandas as pd

logger = logging.getLogger(__name__)


def map_sentinels_to_null(df: pd.DataFrame, sentinels: List) -> pd.DataFrame:
    """Replace sentinel placeholder values with pd.NA across all columns."""
    df_copy = df.copy()

    df_copy = df_copy.replace(sentinels, pd.NA)

    logger.info(f"Sentinel values mapped to null: {sentinels}")

    return df_copy


def type_casting(df: pd.DataFrame) -> pd.DataFrame:
    """Cast Quantity, Price Per Unit, Total Spent, and Transaction Date to their expected types, coercing unparseable values to NaN/NaT."""
    df_copy = df.copy()

    df_copy["Quantity"] = pd.to_numeric(df_copy["Quantity"], errors="coerce").astype(
        "Int64"
    )

    df_copy["Price Per Unit"] = pd.to_numeric(
        df_copy["Price Per Unit"], errors="coerce"
    )

    df_copy["Total Spent"] = pd.to_numeric(df_copy["Total Spent"], errors="coerce")

    df_copy["Transaction Date"] = pd.to_datetime(
        df_copy["Transaction Date"], format="%Y-%m-%d", errors="coerce"
    )

    logger.info(
        "Types casted on 'Quantity', 'Price Per Unit', 'Total Spent' and 'Transaction Date'"
    )

    return df_copy


def derive_total_spent(df: pd.DataFrame) -> pd.DataFrame:
    """Recover missing Total Spent values by multiplying Quantity by Price Per Unit where both are available."""
    df_copy = df.copy()

    recoverable = (
        df_copy["Total Spent"].isna()
        & df_copy["Quantity"].notna()
        & df_copy["Price Per Unit"].notna()
    )

    df_copy.loc[recoverable, "Total Spent"] = (
        df_copy.loc[recoverable, "Quantity"]
        * df_copy.loc[recoverable, "Price Per Unit"]
    )

    recovered_count = recoverable.sum()

    logger.info(f"Recomputed 'Total Spent' on {recovered_count} rows.")

    return df_copy


def remove_nulls_from_critical_fields(
    df: pd.DataFrame, critical_fields: List = None
) -> pd.DataFrame:
    """Drop rows that have a null in any critical field. Defaults to Item, Quantity, Price Per Unit, and Total Spent."""
    if critical_fields is None:
        critical_fields = ["Item", "Quantity", "Price Per Unit", "Total Spent"]

    df_copy = df.copy()

    valid_columns = [col for col in critical_fields if col in df_copy.columns]
    invalid_columns = [col for col in critical_fields if col not in df_copy.columns]

    if invalid_columns:
        logger.warning(f"Columns not found in dataframe: {invalid_columns}.")

    if valid_columns:
        clean_df = df_copy.dropna(subset=valid_columns)
        dropped_rows = len(df_copy) - len(clean_df)
        logger.info(
            f"Nulls were removed from the following columns: {valid_columns}. Dropped rows: {dropped_rows}."
        )

        return clean_df
    else:
        logger.warning(
            "Critical fields were not specified. Cleaning operation did nothing."
        )

        return df_copy


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Run the full cleaning pipeline: sentinel mapping, type casting, total derivation, and null removal."""
    return (
        df.pipe(map_sentinels_to_null, sentinels=["ERROR", "UNKNOWN"])
        .pipe(type_casting)
        .pipe(derive_total_spent)
        .pipe(remove_nulls_from_critical_fields)
    )
