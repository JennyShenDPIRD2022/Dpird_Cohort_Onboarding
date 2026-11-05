"""Load and clean the generated weather data."""

import pandas as pd
import streamlit as st

from weather.config import load_config


def clean_observations(df: pd.DataFrame) -> pd.DataFrame:
    """Deduplicate observations and normalize temperatures to Celsius."""
    cleaned = df.copy()
    cleaned["date"] = pd.to_datetime(cleaned["date"])
    cleaned = cleaned.drop_duplicates(["station_id", "date"], keep="last")
    fahrenheit = cleaned["temp_unit"].eq("F")
    for column in ("max_temp_c", "min_temp_c"):
        cleaned.loc[fahrenheit, column] = (cleaned.loc[fahrenheit, column] - 32) * 5 / 9
    cleaned.loc[fahrenheit, "temp_unit"] = "C"
    return cleaned.sort_values(["station", "date"]).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_stations() -> pd.DataFrame:
    """Load station metadata from the configured CSV file."""
    return pd.read_csv(load_config().paths.stations)


@st.cache_data(show_spinner=False)
def load_daily() -> pd.DataFrame:
    """Load and clean daily weather observations."""
    return clean_observations(pd.read_csv(load_config().paths.daily_weather))