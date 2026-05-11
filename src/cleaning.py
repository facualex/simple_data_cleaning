import logging
from datetime import datetime, timezone
from typing import List, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


def map_sentinels_to_null(
    df: pd.DataFrame, sentinels: List
) -> Tuple[pd.DataFrame, dict]:
    """Replace sentinel placeholder values with pd.NA across all columns."""
    df_copy = df.copy()

    df_copy = df_copy.replace(sentinels, pd.NA)

    affected_columns = {
        col: int((df[col] != df_copy[col]).sum())
        for col in df.columns
        if (df[col] != df_copy[col]).any()
    }

    summary = {
        "sentinels_replaced": sentinels,
        "affected_columns": affected_columns,
    }

    logger.info(f"Sentinel values mapped to null: {sentinels}")

    return df_copy, summary


def type_casting(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """Cast Quantity, Price Per Unit, Total Spent, and Transaction Date to their expected types, coercing unparseable values to NaN/NaT."""
    df_copy = df.copy()

    columns = {
        "Quantity": lambda col: pd.to_numeric(col, errors="coerce").astype("Int64"),
        "Price Per Unit": lambda col: pd.to_numeric(col, errors="coerce"),
        "Total Spent": lambda col: pd.to_numeric(col, errors="coerce"),
        "Transaction Date": lambda col: pd.to_datetime(
            col, format="%Y-%m-%d", errors="coerce"
        ),
    }

    summary = {}

    for col_name, cast_fn in columns.items():
        before_dtype = str(df_copy[col_name].dtype)
        nulls_before = int(df_copy[col_name].isna().sum())

        df_copy[col_name] = cast_fn(df_copy[col_name])

        nulls_after = int(df_copy[col_name].isna().sum())

        summary[col_name] = {
            "before": before_dtype,
            "after": str(df_copy[col_name].dtype),
            "coerced_to_null": nulls_after - nulls_before,
        }

    logger.info(
        "Types casted on 'Quantity', 'Price Per Unit', 'Total Spent' and 'Transaction Date'"
    )

    return df_copy, summary


def derive_total_spent(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
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

    summary = {"total_spent_recovered": int(recovered_count)}

    logger.info(f"Recomputed 'Total Spent' on {recovered_count} rows.")

    return df_copy, summary


def remove_nulls_from_critical_fields(
    df: pd.DataFrame, critical_fields: List = None
) -> tuple[pd.DataFrame, dict]:
    if critical_fields is None:
        critical_fields = ["Item", "Quantity", "Price Per Unit", "Total Spent"]

    df_copy = df.copy()

    valid_columns = [col for col in critical_fields if col in df_copy.columns]
    invalid_columns = [col for col in critical_fields if col not in df_copy.columns]

    if invalid_columns:
        logger.warning("Columns not found in dataframe: %s.", invalid_columns)

    if not valid_columns:
        logger.warning(
            "Critical fields were not specified. Cleaning operation did nothing."
        )
        return df_copy, {}

    nulls_per_field = {col: int(df_copy[col].isna().sum()) for col in valid_columns}

    clean_df = df_copy.dropna(subset=valid_columns)
    dropped_rows = len(df_copy) - len(clean_df)

    summary = {
        "critical_fields": valid_columns,
        "rows_dropped": dropped_rows,
        "nulls_per_field": nulls_per_field,
    }

    logger.info(
        "Dropped %d rows with nulls in critical fields: %s.",
        dropped_rows,
        valid_columns,
    )

    return clean_df, summary


def remove_nulls_from_critical_fields(
    df: pd.DataFrame, critical_fields: List = None
) -> tuple[pd.DataFrame, dict]:
    if critical_fields is None:
        critical_fields = ["Item", "Quantity", "Price Per Unit", "Total Spent"]

    df_copy = df.copy()

    valid_columns = [col for col in critical_fields if col in df_copy.columns]
    invalid_columns = [col for col in critical_fields if col not in df_copy.columns]

    if invalid_columns:
        logger.warning("Columns not found in dataframe: %s.", invalid_columns)

    if not valid_columns:
        logger.warning(
            "Critical fields were not specified. Cleaning operation did nothing."
        )
        return df_copy, {}

    nulls_per_field = {col: int(df_copy[col].isna().sum()) for col in valid_columns}

    clean_df = df_copy.dropna(subset=valid_columns)

    summary = {
        "critical_fields": valid_columns,
        "rows_dropped": len(df_copy) - len(clean_df),
        "nulls_per_field": nulls_per_field,
    }

    logger.info(
        "Dropped %d rows with nulls in critical fields: %s.",
        summary["rows_dropped"],
        valid_columns,
    )

    return clean_df, summary


def clean(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """Run the full cleaning pipeline: sentinel mapping, type casting, total derivation, and null removal."""
    cleaning_report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rows_before": len(df),
        "rows_after": 0,
        "rows_dropped": 0,
        "map_sentinels_to_null": {},
        "type_casting": {},
        "derive_total_spent": {},
        "remove_nulls_from_critical_fields": {},
    }

    sentinels_to_null_df, summary = map_sentinels_to_null(df, ["ERROR", "UNKNOWN"])
    cleaning_report["map_sentinels_to_null"] = summary

    type_casting_df, summary = type_casting(sentinels_to_null_df)
    cleaning_report["type_casting"] = summary

    calculated_total_df, summary = derive_total_spent(type_casting_df)
    cleaning_report["derive_total_spent"] = summary

    remove_nulls_df, summary = remove_nulls_from_critical_fields(calculated_total_df)
    cleaning_report["remove_nulls_from_critical_fields"] = summary

    rows_after = len(remove_nulls_df)

    cleaning_report["rows_after"] = rows_after
    cleaning_report["rows_dropped"] = len(df) - rows_after

    return remove_nulls_df, cleaning_report
