"""Compare synthetic rainfall across stations and time."""

import streamlit as st

from weather.app_logic import rainfall_comparison_days, rainfall_station_summary
from weather.charts import rainfall_comparison_chart, rainfall_heatmap_chart, rainfall_station_totals_chart
from weather.data import load_daily, load_stations
from weather.metrics import rainfall_period_totals
from weather.ui import configure_page, footer, synthetic_notice

configure_page("Rainfall explorer · WA Weather Tracker")
st.title("Rainfall explorer")
st.write("Compare rainfall patterns across locations and see when the rain arrived.")
synthetic_notice()

try:
    daily = load_daily()
    stations = load_stations()
except FileNotFoundError:
    st.error("Weather data is not available yet. Run `python scripts/generate_data.py` first.")
    footer()
    st.stop()

if daily.empty or stations.empty or daily["date"].dropna().empty:
    st.info("No observations or stations are available to explore.")
    footer()
    st.stop()

with st.sidebar:
    st.header("Rainfall filters")
    regions = sorted(stations["region"].unique())
    selected_regions = st.multiselect("Regions", regions, default=regions)
    available_stations = sorted(stations.loc[stations["region"].isin(selected_regions), "station"].unique())
    selected_stations = st.multiselect("Stations", available_stations, default=available_stations)
    selected_dates = st.date_input(
        "Date range",
        value=(daily["date"].min().date(), daily["date"].max().date()),
        min_value=daily["date"].min().date(),
        max_value=daily["date"].max().date(),
        format="DD/MM/YYYY",
    )
    frequency = st.selectbox("Time interval", ["Daily", "Weekly", "Monthly"], index=2)

if not selected_regions or not selected_stations or len(selected_dates) != 2:
    st.info("Choose at least one region, one station and a complete date range to explore rainfall.")
    footer()
    st.stop()

start_date, end_date = selected_dates
if end_date < start_date:
    st.info("Choose an end date on or after the start date.")
    footer()
    st.stop()

comparison = rainfall_comparison_days(daily, selected_stations, start_date, end_date)
observed_days = int(comparison["rainfall_mm"].count())
expected_days = len(comparison)
facts = st.columns(3)
facts[0].metric("Stations compared", len(selected_stations))
facts[1].metric("Days in selection", (end_date - start_date).days + 1)
facts[2].metric("Observation coverage", f"{100 * observed_days / expected_days:.1f}%")
st.caption("Coverage is the share of selected station-days with a rainfall observation.")

if observed_days < expected_days:
    st.warning(
        f"{expected_days - observed_days:,} of {expected_days:,} selected station-days have no rainfall observation. "
        "Totals include observed rainfall only; stations with lower coverage may appear drier."
    )
st.caption(
    "Missing rainfall is not zero. Entirely unobserved periods remain gaps; partially observed periods "
    "show the sum of available observations. Rain days have more than 0 mm."
)

st.subheader("Station comparison")
summary = rainfall_station_summary(comparison)
if observed_days > 0:
    st.plotly_chart(rainfall_station_totals_chart(summary), use_container_width=True)
    st.caption(
        "Selected stations ranked by observed rainfall, highest first; ties are alphabetical. "
        "Totals use the selected dates, regardless of time interval. Hover over bars for coverage. "
        "Stations without observations are listed last and are not ranked as dry."
    )
st.dataframe(
    summary,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Observed rainfall (mm)": st.column_config.NumberColumn(format="%.1f mm"),
        "Wettest day (mm)": st.column_config.NumberColumn(format="%.1f mm"),
        "Coverage (%)": st.column_config.NumberColumn(format="%.1f%%"),
        "Rain days (>0 mm)": st.column_config.NumberColumn(format="%d"),
    },
)

if observed_days == 0:
    st.info("No rainfall observations are available for these stations and dates. Try a different selection.")
    footer()
    st.stop()

st.subheader("Rainfall over time")
view = st.radio("Rainfall view", ["Period totals", "Cumulative observed rainfall"], horizontal=True)
periods = rainfall_period_totals(comparison, frequency)
st.plotly_chart(
    rainfall_comparison_chart(periods, cumulative=view == "Cumulative observed rainfall"),
    use_container_width=True,
)
st.caption(
    "Weeks start on Monday. First and last periods use only dates inside your selection. "
    "Cumulative rainfall restarts at the selected start date, skips missing observations and resumes "
    "from the last observed total; it is not an estimate of rainfall during gaps."
)

st.subheader("Monthly rainfall patterns")
st.plotly_chart(
    rainfall_heatmap_chart(rainfall_period_totals(comparison, "Monthly")),
    use_container_width=True,
)
st.caption("Darker cells indicate less observed rain; blank cells mean no observations. Hover to inspect coverage.")
footer()
