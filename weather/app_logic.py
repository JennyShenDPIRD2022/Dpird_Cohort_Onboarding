"""Data preparation for the Streamlit pages."""

from dataclasses import dataclass
from datetime import date

import pandas as pd

from weather.metrics import frost_nights, heat_days, monthly_rainfall


@dataclass(frozen=True)
class OverviewKpis:
    """Headline values for the overview page."""

    total_rainfall: float
    wettest_station: str
    hottest_day: str
    frost_nights: int


def filter_observations(
    df: pd.DataFrame, regions: list[str], start_date: date, end_date: date
) -> pd.DataFrame:
    """Filter observations by selected regions and inclusive dates."""
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    return df[df["region"].isin(regions) & df["date"].between(start, end)].copy()


def overview_kpis(df: pd.DataFrame, frost_threshold: float) -> OverviewKpis:
    """Calculate the four overview headline values."""
    station_rain = df.groupby("station")["rainfall_mm"].sum(min_count=1).dropna()
    wettest = station_rain.idxmax() if not station_rain.empty else "Not available"
    valid_heat = df.dropna(subset=["max_temp_c"])
    if valid_heat.empty:
        hottest = "Not available"
    else:
        row = valid_heat.loc[valid_heat["max_temp_c"].idxmax()]
        hottest = f"{row['station']} · {row['max_temp_c']:.1f} °C"
    return OverviewKpis(
        total_rainfall=float(df["rainfall_mm"].sum()),
        wettest_station=str(wettest),
        hottest_day=hottest,
        frost_nights=frost_nights(df, frost_threshold),
    )


def region_rainfall(df: pd.DataFrame) -> pd.DataFrame:
    """Return monthly rainfall totals by region."""
    return monthly_rainfall(df, "region")


def daily_temperatures(df: pd.DataFrame) -> pd.DataFrame:
    """Return daily average maximum and minimum temperatures."""
    return (
        df.groupby("date", as_index=False)[["max_temp_c", "min_temp_c"]]
        .mean()
        .sort_values("date")
    )


def map_totals(df: pd.DataFrame, stations: pd.DataFrame) -> pd.DataFrame:
    """Join selected-period station rainfall totals to map coordinates."""
    totals = df.groupby("station_id", as_index=False)["rainfall_mm"].sum(min_count=1)
    return stations.merge(totals, on="station_id", how="inner")


def station_monthly_summary(
    df: pd.DataFrame, frost_threshold: float, heat_threshold: float
) -> pd.DataFrame:
    """Build a monthly station summary with rain and temperature events."""
    rows: list[dict[str, object]] = []
    for month, month_data in df.groupby(df["date"].dt.to_period("M")):
        rows.append(
            {
                "Month": month.to_timestamp(),
                "Rainfall (mm)": month_data["rainfall_mm"].sum(min_count=1),
                "Mean max (°C)": month_data["max_temp_c"].mean(),
                "Mean min (°C)": month_data["min_temp_c"].mean(),
                "Frost nights": frost_nights(month_data, frost_threshold),
                "Heat days": heat_days(month_data, heat_threshold),
            }
        )
    return pd.DataFrame(rows)


def rainfall_comparison_days(
    df: pd.DataFrame, stations: list[str], start_date: date, end_date: date
) -> pd.DataFrame:
    """Return selected station/day pairs, retaining absent observations as missing values."""
    if end_date < start_date:
        raise ValueError("The end date must be on or after the start date.")
    selected = df.loc[
        df["station"].isin(stations) & df["date"].between(pd.Timestamp(start_date), pd.Timestamp(end_date)),
        ["station", "date", "rainfall_mm"],
    ]
    grid = pd.MultiIndex.from_product(
        [sorted(set(stations)), pd.date_range(start_date, end_date, freq="D")],
        names=["station", "date"],
    )
    return selected.set_index(["station", "date"]).reindex(grid).reset_index()


def rainfall_station_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Compare observed rainfall and coverage on a complete station/day grid."""
    grouped = df.groupby("station")["rainfall_mm"]
    summary = grouped.agg(
        total=lambda values: values.sum(min_count=1),
        observed="count",
        expected="size",
        rain_days=lambda values: values.gt(0).sum() if values.notna().any() else float("nan"),
        wettest="max",
    )
    summary["coverage"] = summary["observed"] / summary["expected"] * 100
    return (
        summary.rename(
            columns={
                "total": "Observed rainfall (mm)",
                "observed": "Observed days",
                "expected": "Days in selection",
                "rain_days": "Rain days (>0 mm)",
                "wettest": "Wettest day (mm)",
                "coverage": "Coverage (%)",
            }
        )
        .rename_axis("Station")
        .reset_index()
        .sort_values(["Observed rainfall (mm)", "Station"], ascending=[False, True], na_position="last")
        .reset_index(drop=True)
    )