"""Summarise interval rainfall readings into monthly station totals."""

import argparse
from collections import defaultdict
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]


def configured_paths() -> tuple[Path, Path]:
    """Read the default input and output paths from config.yaml."""
    with (ROOT / "config.yaml").open(encoding="utf-8") as config_file:
        paths = yaml.safe_load(config_file)["paths"]
    return ROOT / paths["rainfall_readings"], ROOT / paths["monthly_rainfall"]


def monthly_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Accumulate monthly rainfall totals for each station."""
    totals: defaultdict[tuple[str, str], float] = defaultdict(float)
    station_details: dict[str, tuple[str, str]] = {}

    for _, row in df.iterrows():
        timestamp = pd.to_datetime(row["timestamp"])
        month = timestamp.strftime("%Y-%m")
        station = str(row["station"])
        station_details[station] = (str(row["station_id"]), str(row["region"]))
        if not pd.isna(row["rainfall_mm"]):
            totals[(station, month)] += float(row["rainfall_mm"])

    rows = []
    for (station, month), rainfall in totals.items():
        station_id, region = station_details[station]
        rows.append(
            {
                "station_id": station_id,
                "station": station,
                "region": region,
                "month": month,
                "rainfall_mm": round(rainfall, 1),
            }
        )
    return pd.DataFrame(rows).sort_values(["month", "station"]).reset_index(drop=True)


def parse_args() -> argparse.Namespace:
    """Parse command-line input and output options."""
    default_input, default_output = configured_paths()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=default_input)
    parser.add_argument("--output", type=Path, default=default_output)
    return parser.parse_args()


def main() -> None:
    """Read gauge data, calculate monthly totals, and write a CSV."""
    args = parse_args()
    readings = pd.read_csv(args.input)
    summary = monthly_totals(readings)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output, index=False)
    print(
        f"Summarised {len(readings):,} readings into {len(summary):,} station-months "
        f"for {summary['station'].nunique()} stations."
    )
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()