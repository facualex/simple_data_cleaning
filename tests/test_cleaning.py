import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cleaning import (
    clean,
    derive_total_spent,
    map_sentinels_to_null,
    remove_nulls_from_critical_fields,
    type_casting,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _raw_df(**overrides):
    """Minimal string-typed DataFrame matching the CSV schema (pre type_casting)."""
    data = {
        "Item": ["Coffee"],
        "Quantity": ["2"],
        "Price Per Unit": ["2.0"],
        "Total Spent": ["4.0"],
        "Transaction Date": ["2023-01-01"],
    }
    data.update(overrides)
    return pd.DataFrame(data)


def _typed_df(**overrides):
    """Minimal DataFrame with types already applied (post type_casting)."""
    data = {
        "Item": ["Coffee"],
        "Quantity": pd.array([2], dtype="Int64"),
        "Price Per Unit": [2.0],
        "Total Spent": [4.0],
        "Transaction Date": pd.to_datetime(["2023-01-01"]),
    }
    data.update(overrides)
    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# map_sentinels_to_null
# ---------------------------------------------------------------------------


class TestMapSentinelsToNull:
    def test_replaces_sentinels_with_na(self):
        df = pd.DataFrame({"A": ["ERROR", "ok"], "B": ["UNKNOWN", "ok"]})
        result = map_sentinels_to_null(df, sentinels=["ERROR", "UNKNOWN"])
        assert pd.isna(result.loc[0, "A"])
        assert pd.isna(result.loc[0, "B"])

    def test_preserves_non_sentinel_values(self):
        df = pd.DataFrame({"A": ["ERROR", "valid"], "B": [1, 2]})
        result = map_sentinels_to_null(df, sentinels=["ERROR"])
        assert result.loc[1, "A"] == "valid"
        assert list(result["B"]) == [1, 2]

    def test_replaces_across_all_columns(self):
        df = pd.DataFrame({"A": ["ERROR"], "B": ["ERROR"], "C": ["ERROR"]})
        result = map_sentinels_to_null(df, sentinels=["ERROR"])
        for col in ["A", "B", "C"]:
            assert pd.isna(result.loc[0, col])

    def test_empty_sentinel_list_changes_nothing(self):
        df = pd.DataFrame({"A": ["ERROR", "UNKNOWN"]})
        result = map_sentinels_to_null(df, sentinels=[])
        pd.testing.assert_frame_equal(result, df)

    def test_does_not_mutate_input(self):
        df = pd.DataFrame({"A": ["ERROR"]})
        original = df.copy()
        map_sentinels_to_null(df, sentinels=["ERROR"])
        pd.testing.assert_frame_equal(df, original)


# ---------------------------------------------------------------------------
# type_casting
# ---------------------------------------------------------------------------


class TestTypeCasting:
    def test_quantity_cast_to_int64(self):
        result = type_casting(_raw_df())
        assert result["Quantity"].dtype == pd.Int64Dtype()

    def test_price_per_unit_cast_to_float(self):
        result = type_casting(_raw_df())
        assert result["Price Per Unit"].dtype == float

    def test_total_spent_cast_to_float(self):
        result = type_casting(_raw_df())
        assert result["Total Spent"].dtype == float

    def test_transaction_date_cast_to_datetime(self):
        result = type_casting(_raw_df())
        assert pd.api.types.is_datetime64_any_dtype(result["Transaction Date"])

    def test_unparseable_numeric_values_become_null(self):
        df = _raw_df(**{
            "Quantity": ["bad"],
            "Price Per Unit": ["bad"],
            "Total Spent": ["bad"],
        })
        result = type_casting(df)
        assert pd.isna(result.loc[0, "Quantity"])
        assert pd.isna(result.loc[0, "Price Per Unit"])
        assert pd.isna(result.loc[0, "Total Spent"])

    def test_wrong_date_format_becomes_null(self):
        # pipeline uses strict %Y-%m-%d; other formats must not silently parse
        df = _raw_df(**{"Transaction Date": ["01/01/2023"]})
        result = type_casting(df)
        assert pd.isna(result.loc[0, "Transaction Date"])

    def test_unparseable_date_becomes_null(self):
        df = _raw_df(**{"Transaction Date": ["not-a-date"]})
        result = type_casting(df)
        assert pd.isna(result.loc[0, "Transaction Date"])

    def test_does_not_mutate_input(self):
        df = _raw_df()
        original = df.copy()
        type_casting(df)
        pd.testing.assert_frame_equal(df, original)


# ---------------------------------------------------------------------------
# derive_total_spent
# ---------------------------------------------------------------------------


class TestDeriveTotalSpent:
    def test_fills_missing_total_spent_from_quantity_and_price(self):
        df = _typed_df(**{"Total Spent": [float("nan")]})
        result = derive_total_spent(df)
        assert result.loc[0, "Total Spent"] == pytest.approx(4.0)

    def test_derives_correct_value(self):
        df = _typed_df(**{
            "Quantity": pd.array([3], dtype="Int64"),
            "Price Per Unit": [5.0],
            "Total Spent": [float("nan")],
        })
        result = derive_total_spent(df)
        assert result.loc[0, "Total Spent"] == pytest.approx(15.0)

    def test_does_not_overwrite_existing_total_spent(self):
        df = _typed_df(**{"Total Spent": [99.0]})
        result = derive_total_spent(df)
        assert result.loc[0, "Total Spent"] == pytest.approx(99.0)

    def test_leaves_null_when_quantity_is_missing(self):
        df = _typed_df(**{
            "Quantity": pd.array([pd.NA], dtype="Int64"),
            "Total Spent": [float("nan")],
        })
        result = derive_total_spent(df)
        assert pd.isna(result.loc[0, "Total Spent"])

    def test_leaves_null_when_price_per_unit_is_missing(self):
        df = _typed_df(**{
            "Price Per Unit": [float("nan")],
            "Total Spent": [float("nan")],
        })
        result = derive_total_spent(df)
        assert pd.isna(result.loc[0, "Total Spent"])

    def test_does_not_mutate_input(self):
        df = _typed_df(**{"Total Spent": [float("nan")]})
        original = df.copy()
        derive_total_spent(df)
        pd.testing.assert_frame_equal(df, original)


# ---------------------------------------------------------------------------
# remove_nulls_from_critical_fields
# ---------------------------------------------------------------------------


class TestRemoveNullsFromCriticalFields:
    def _df_with_nulls(self):
        return pd.DataFrame({
            "Item": ["Coffee", None, "Tea"],
            "Quantity": pd.array([2, 3, pd.NA], dtype="Int64"),
            "Price Per Unit": [2.0, 3.0, 1.5],
            "Total Spent": [4.0, 9.0, float("nan")],
        })

    def test_drops_rows_with_null_in_default_critical_fields(self):
        result = remove_nulls_from_critical_fields(self._df_with_nulls())
        assert len(result) == 1
        assert result.iloc[0]["Item"] == "Coffee"

    def test_keeps_rows_with_no_nulls_in_critical_fields(self):
        df = pd.DataFrame({
            "Item": ["Coffee", "Tea"],
            "Quantity": pd.array([1, 2], dtype="Int64"),
            "Price Per Unit": [1.0, 2.0],
            "Total Spent": [1.0, 4.0],
        })
        result = remove_nulls_from_critical_fields(df)
        assert len(result) == 2

    def test_accepts_custom_critical_fields(self):
        df = pd.DataFrame({"A": [1, None, 3], "B": [None, 2, 3]})
        result = remove_nulls_from_critical_fields(df, critical_fields=["A"])
        assert len(result) == 2
        assert result["A"].notna().all()

    def test_ignores_columns_not_present_in_dataframe(self):
        df = pd.DataFrame({
            "Item": ["Coffee", None],
            "Quantity": pd.array([1, 2], dtype="Int64"),
            "Price Per Unit": [1.0, 2.0],
            "Total Spent": [1.0, 2.0],
        })
        result = remove_nulls_from_critical_fields(
            df, critical_fields=["Item", "Nonexistent"]
        )
        assert len(result) == 1

    def test_returns_unchanged_df_when_all_critical_fields_are_absent(self):
        df = pd.DataFrame({"A": [1, 2]})
        result = remove_nulls_from_critical_fields(df, critical_fields=["Nonexistent"])
        pd.testing.assert_frame_equal(result, df)

    def test_does_not_mutate_input(self):
        df = self._df_with_nulls()
        original = df.copy()
        remove_nulls_from_critical_fields(df)
        pd.testing.assert_frame_equal(df, original)


# ---------------------------------------------------------------------------
# clean (integration)
# ---------------------------------------------------------------------------


class TestClean:
    def _dirty_df(self):
        return pd.DataFrame({
            "Item": ["Coffee", "UNKNOWN", None, "Tea"],
            "Quantity": ["2", "3", "1", "ERROR"],
            "Price Per Unit": ["2.0", "3.0", "1.5", "1.5"],
            "Total Spent": ["ERROR", "9.0", "1.5", "3.0"],
            "Transaction Date": ["2023-01-01", "2023-06-15", "2023-03-20", "2023-12-31"],
        })

    def test_no_nulls_in_critical_fields_after_cleaning(self):
        result = clean(self._dirty_df())
        for col in ["Item", "Quantity", "Price Per Unit", "Total Spent"]:
            assert result[col].notna().all(), f"Unexpected nulls in {col}"

    def test_sentinel_strings_are_not_present_in_output(self):
        result = clean(self._dirty_df())
        for col in result.select_dtypes("str").columns:
            assert "ERROR" not in result[col].values
            assert "UNKNOWN" not in result[col].values

    def test_output_columns_have_correct_types(self):
        result = clean(self._dirty_df())
        assert result["Quantity"].dtype == pd.Int64Dtype()
        assert result["Price Per Unit"].dtype == float
        assert result["Total Spent"].dtype == float
        assert pd.api.types.is_datetime64_any_dtype(result["Transaction Date"])

    def test_total_spent_is_recovered_when_derivable(self):
        df = pd.DataFrame({
            "Item": ["Coffee"],
            "Quantity": ["3"],
            "Price Per Unit": ["5.0"],
            "Total Spent": ["ERROR"],
            "Transaction Date": ["2023-01-01"],
        })
        result = clean(df)
        assert len(result) == 1
        assert result.iloc[0]["Total Spent"] == pytest.approx(15.0)

    def test_rows_without_recoverable_critical_fields_are_dropped(self):
        df = pd.DataFrame({
            "Item": ["Coffee"],
            "Quantity": ["ERROR"],
            "Price Per Unit": ["ERROR"],
            "Total Spent": ["ERROR"],
            "Transaction Date": ["2023-01-01"],
        })
        result = clean(df)
        assert len(result) == 0

    def test_does_not_mutate_input(self):
        df = self._dirty_df()
        original = df.copy()
        clean(df)
        pd.testing.assert_frame_equal(df, original)
