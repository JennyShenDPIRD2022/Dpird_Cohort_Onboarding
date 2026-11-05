"""Generate deterministic synthetic weather data for the demo application."""

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
SEED = 2024

STATIONS = [
    ("WA001", "Kununurra", "Kimberley", -15.778, 128.710, 47, 34.0, 22.0, 3.2, 0.04, 0.33, 7.5, 0.00, 0.32),
    ("WA002", "Port Hedland", "Pilbara", -20.310, 118.626, 13, 33.2, 21.5, 4.2, 0.025, 0.14, 5.2, 0.00, 0.27),
    ("WA003", "Carnarvon", "Gascoyne", -24.880, 113.672, 8, 28.1, 17.0, 4.8, 0.035, 0.09, 3.6, 0.00, 0.12),
    ("WA004", "Geraldton", "Mid West", -28.777, 114.614, 34, 25.3, 14.2, 5.0, 0.055, 0.23, 3.8, 0.00, 0.05),
    ("WA005", "Moora", "Wheatbelt", -30.641, 116.010, 203, 25.7, 12.0, 6.8, 0.045, 0.18, 3.2, 0.10, 0.18),
    ("WA006", "Merredin", "Wheatbelt", -31.482, 118.279, 315, 25.6, 11.1, 7.4, 0.035, 0.13, 2.7, 0.20, 0.27),
    ("WA007", "Northam", "Wheatbelt", -31.654, 116.670, 170, 25.2, 11.4, 7.0, 0.045, 0.17, 3.0, 0.17, 0.22),
    ("WA008", "Katanning", "Great Southern", -33.691, 117.556, 310, 21.9, 9.5, 6.2, 0.055, 0.20, 3.1, 0.18, 0.09),
    ("WA009", "Albany", "Great Southern", -35.027, 117.884, 69, 19.7, 11.6, 4.0, 0.10, 0.28, 4.0, 0.01, 0.01),
    ("WA010", "Manjimup", "South West", -34.241, 116.146, 287, 21.0, 10.1, 5.2, 0.10, 0.31, 4.5, 0.10, 0.03),
    ("WA011", "Busselton", "South West", -33.650, 115.345, 4, 22.1, 12.0, 4.6, 0.09, 0.30, 4.6, 0.01, 0.02),
    ("WA012", "Esperance", "Goldfields-Esperance", -33.861, 121.891, 25, 21.5, 11.7, 4.4, 0.08, 0.22, 3.5, 0.02, 0.03),
]

STATION_COLUMNS = [
    "station_id", "station", "region", "lat", "lon", "elevation_m",
    "annual_max", "annual_min", "temp_amplitude", "rain_base", "rain_seasonal",
    "rain_scale", "frost_chance", "heat_chance",
]


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--interval-minutes",
        type=int,
        default=10,
        help="Rain-gauge interval in minutes (default: 10)",
    )
    return parser.parse_args()


def configured_paths() -> dict[str, Path]:
    """Read generated-data paths from config.yaml."""
    with (ROOT / "config.yaml").open(encoding="utf-8") as config_file:
        raw = yaml.safe_load(config_file)
    return {name: ROOT / value for name, value in raw["paths"].items()}


def station_frame() -> pd.DataFrame:
    """Return public station metadata and internal climate profiles."""
    return pd.DataFrame(STATIONS, columns=STATION_COLUMNS)


def generate_daily(stations: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Create one synthetic daily observation per station and date."""
    rows: list[dict[str, object]] = []
    dates = pd.date_range("2024-01-01", "2024-12-31", freq="D")

    for station in stations.itertuples(index=False):
        for date in dates:
            summer = math.cos(2 * math.pi * (date.dayofyear - 15) / 366)
            winter_strength = (1 - summer) / 2
            summer_strength = (1 + summer) / 2
            max_temp = station.annual_max + station.temp_amplitude * summer + rng.normal(0, 2.0)
            min_temp = station.annual_min + station.temp_amplitude * 0.65 * summer + rng.normal(0, 1.5)

            if date.month in (6, 7, 8) and rng.random() < station.frost_chance:
                min_temp = rng.uniform(-1.5, 1.9)
            if date.month in (12, 1, 2) and rng.random() < station.heat_chance:
                max_temp = 35 + rng.gamma(2.0, 2.0)
            max_temp = max(max_temp, min_temp + 3.0)

            if station.region in {"Kimberley", "Pilbara", "Gascoyne"}:
                rain_chance = station.rain_base + station.rain_seasonal * summer_strength**2
            else:
                rain_chance = station.rain_base + station.rain_seasonal * winter_strength**2
            rainfall = rng.gamma(1.35, station.rain_scale) if rng.random() < rain_chance else 0.0

            rows.append(
                {
                    "date": date,
                    "station_id": station.station_id,
                    "station": station.station,
                    "region": station.region,
                    "rainfall_mm": round(rainfall, 1),
                    "max_temp_c": round(max_temp, 1),
                    "min_temp_c": round(min_temp, 1),
                    "temp_unit": "C",
                }
            )

    daily = pd.DataFrame(rows)
    for column in ("rainfall_mm", "max_temp_c", "min_temp_c"):
        missing_indices = rng.choice(daily.index, size=14, replace=False)
        daily.loc[missing_indices, column] = np.nan

    fahrenheit = (daily["station"] == "Albany") & (daily["date"].dt.month == 7)
    daily.loc[fahrenheit, "max_temp_c"] = daily.loc[fahrenheit, "max_temp_c"] * 9 / 5 + 32
    daily.loc[fahrenheit, "min_temp_c"] = daily.loc[fahrenheit, "min_temp_c"] * 9 / 5 + 32
    daily.loc[fahrenheit, "temp_unit"] = "F"

    duplicate_indices = rng.choice(daily.index, size=8, replace=False)
    return pd.concat([daily, daily.loc[duplicate_indices]], ignore_index=True)


def generate_rainfall_readings(
    daily: pd.DataFrame,
    interval_minutes: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Split each daily rainfall total across regular gauge readings."""
    readings: list[dict[str, object]] = []
    observations = daily.drop_duplicates(["station_id", "date"], keep="last")
    periods = 1440 // interval_minutes

    for row in observations.itertuples(index=False):
        timestamps = pd.date_range(row.date, periods=periods, freq=f"{interval_minutes}min")
        amounts = np.zeros(periods)
        if pd.isna(row.rainfall_mm):
            amounts[:] = np.nan
        elif row.rainfall_mm > 0:
            event_count = min(periods, int(rng.integers(1, 9)))
            event_indices = rng.choice(periods, size=event_count, replace=False)
            amounts[event_indices] = rng.dirichlet(np.ones(event_count)) * row.rainfall_mm

        readings.extend(
            {
                "timestamp": timestamp,
                "station_id": row.station_id,
                "station": row.station,
                "region": row.region,
                "rainfall_mm": amount,
            }
            for timestamp, amount in zip(timestamps, amounts, strict=True)
        )

    return pd.DataFrame(readings)


def main() -> None:
    """Generate and write all synthetic CSV files."""
    args = parse_args()
    if args.interval_minutes <= 0 or 1440 % args.interval_minutes != 0:
        raise SystemExit("--interval-minutes must be a positive divisor of 1440")

    paths = configured_paths()
    paths["stations"].parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    stations = station_frame()
    daily = generate_daily(stations, rng)
    rainfall = generate_rainfall_readings(daily, args.interval_minutes, rng)

    stations[STATION_COLUMNS[:6]].to_csv(paths["stations"], index=False)
    daily.to_csv(paths["daily_weather"], index=False, date_format="%Y-%m-%d")
    rainfall.to_csv(paths["rainfall_readings"], index=False, date_format="%Y-%m-%d %H:%M:%S")
    print(
        f"Generated {len(stations)} stations, {len(daily):,} daily rows, "
        f"and {len(rainfall):,} gauge readings at {args.interval_minutes}-minute intervals."
    )


if __name__ == "__main__":
    main()