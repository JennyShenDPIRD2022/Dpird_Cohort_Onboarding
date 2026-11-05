"""Weather metrics used by the app and tests."""

from collections import defaultdict
from typing import Literal

import pandas as pd


def calc_gdd(df: pd.DataFrame, base_c: float) -> pd.DataFrame:
    """Calculate daily and cumulative growing degree days by station."""
    result = df.copy().sort_values(["station", "date"])
    daily_values: list[float] = []
    cumulative_values: list[float] = []
    running_totals: defaultdict[str, float] = defaultdict(float)

    for _, row in result.iterrows():
        station = str(row["station"])
        if pd.isna(row["max_temp_c"]) or pd.isna(row["min_temp_c"]):
            daily_values.append(float("nan"))
        else:
            daily_gdd = max(0.0, (row["max_temp_c"] + row["min_temp_c"]) / 2 - base_c)
            daily_values.append(daily_gdd)
            running_totals[station] += daily_gdd
        cumulative_values.append(running_totals[station])

    result["gdd"] = daily_values
    result["cumulative_gdd"] = cumulative_values
    return result


def frost_nights(df: pd.DataFrame, threshold_c: float) -> int:
    """Count nights colder than the configured frost threshold."""
    return int(df["min_temp_c"].lt(threshold_c).sum())


def heat_days(df: pd.DataFrame, threshold_c: float) -> int:
    """Count days at or above the configured heat threshold."""
    return int(df["max_temp_c"].ge(threshold_c).sum())


def monthly_rainfall(df: pd.DataFrame, group_by: str) -> pd.DataFrame:
    """Aggregate valid rainfall observations by month and one category."""
    monthly = df.assign(month=df["date"].dt.to_period("M").dt.to_timestamp())
    return (
        monthly.groupby(["month", group_by], as_index=False)["rainfall_mm"]
        .sum(min_count=1)
        .sort_values(["month", group_by])
    )


def rainfall_period_totals(
    df: pd.DataFrame, frequency: Literal["Daily", "Weekly", "Monthly"]
) -> pd.DataFrame:
    """Summarize a complete station/day grid; weeks start Monday, missing totals remain NaN."""
    periods = {"Daily": "D", "Weekly": "W-SUN", "Monthly": "M"}
    dated = df.assign(period=df["date"].dt.to_period(periods[frequency]).dt.to_timestamp())
    grouped = dated.groupby(["station", "period"])["rainfall_mm"]
    result = grouped.agg(
        rainfall_mm=lambda values: values.sum(min_count=1),
        observed_days="count",
        expected_days="size",
    ).reset_index()
    result = result.sort_values(["station", "period"]).reset_index(drop=True)
    result["cumulative_rainfall_mm"] = result.groupby("station")["rainfall_mm"].cumsum()
    return result