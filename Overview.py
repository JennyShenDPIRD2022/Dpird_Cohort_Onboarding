"""Overview page for WA Weather Tracker."""

import streamlit as st

from weather.app_logic import (
    daily_temperatures,
    filter_observations,
    map_totals,
    overview_kpis,
    region_rainfall,
)
from weather.charts import monthly_rainfall_chart, station_map_chart, temperature_trend_chart
from weather.config import load_config
from weather.data import load_daily, load_stations
from weather.ui import configure_page, footer, synthetic_notice

configure_page("WA Weather Tracker")
config = load_config()

st.title("WA Weather Tracker")
st.write("Explore rainfall and temperature patterns across Western Australia in 2024.")
synthetic_notice()

try:
    daily = load_daily()
    stations = load_stations()
except FileNotFoundError:
    st.error("Weather data is not available yet. Run `python scripts/generate_data.py` first.")
    st.stop()

all_regions = sorted(daily["region"].unique())
with st.sidebar:
    st.header("Filters")
    selected_regions = st.multiselect("Region", all_regions, default=all_regions)
    selected_dates = st.date_input(
        "Date range",
        value=(daily["date"].min().date(), daily["date"].max().date()),
        min_value=daily["date"].min().date(),
        max_value=daily["date"].max().date(),
        format="DD/MM/YYYY",
    )

if len(selected_dates) != 2 or not selected_regions:
    st.info("Choose at least one region and a complete date range to explore the weather.")
    footer()
    st.stop()

filtered = filter_observations(daily, selected_regions, selected_dates[0], selected_dates[1])
if filtered.empty:
    st.info("No observations match those filters. Try a wider date range or another region.")
    footer()
    st.stop()

kpis = overview_kpis(filtered, config.thresholds.frost_c)
columns = st.columns(4)
columns[0].metric("Total rainfall", f"{kpis.total_rainfall:,.0f} mm")
columns[1].metric("Wettest station", kpis.wettest_station)
columns[2].metric("Hottest day", kpis.hottest_day)
columns[3].metric("Frost nights", f"{kpis.frost_nights:,}")

st.subheader("Rainfall through the year")
st.plotly_chart(monthly_rainfall_chart(region_rainfall(filtered)), use_container_width=True)

st.subheader("Daily temperature across selected stations")
st.plotly_chart(temperature_trend_chart(daily_temperatures(filtered)), use_container_width=True)

st.subheader("Weather stations")
st.plotly_chart(station_map_chart(map_totals(filtered, stations)), use_container_width=True)



# Display footer with all of the different options and footr menuat the end of the page



footer()