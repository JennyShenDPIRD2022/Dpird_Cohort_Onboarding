"""Application configuration loaded from the project YAML file."""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Paths:
    """Resolved input and output paths."""

    stations: Path
    daily_weather: Path
    rainfall_readings: Path
    monthly_rainfall: Path
    station_rankings: Path


@dataclass(frozen=True)
class Thresholds:
    """Weather thresholds in degrees Celsius."""

    frost_c: float
    heat_c: float
    gdd_base_c: float


@dataclass(frozen=True)
class Config:
    """Complete application configuration."""

    paths: Paths
    thresholds: Thresholds


@lru_cache(maxsize=1)
def load_config() -> Config:
    """Load and resolve settings from config.yaml."""
    with (ROOT / "config.yaml").open(encoding="utf-8") as config_file:
        raw = yaml.safe_load(config_file)

    paths = {name: ROOT / value for name, value in raw["paths"].items()}
    return Config(paths=Paths(**paths), thresholds=Thresholds(**raw["thresholds"]))