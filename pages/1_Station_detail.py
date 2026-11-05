"""Station detail page for WA Weather Tracker."""

import streamlit as st

from weather.app_logic import station_monthly_summary
from weather.charts import gdd_chart, station_weather_chart
from weather.config import load_config
from weather.data import load_daily, load_stations
from weather.metrics import calc_gdd
from weather.ui import configure_page, footer, synthetic_notice

configure_page("Station detail · WA Weather Tracker")
config = load_config()

st.title("Station detail")
st.write("Follow rainfall, temperature and growing conditions at one location.")
synthetic_notice()

try:
    daily = load_daily()
    stations = load_stations()
except FileNotFoundError:
    st.error("Weather data is not available yet. Run `python scripts/generate_data.py` first.")
    st.stop()

station_name = st.selectbox("Weather station", sorted(daily["station"].unique()))
station_daily = daily[daily["station"] == station_name].copy()
station = stations.loc[stations["station"] == station_name].iloc[0]

if station_daily.empty:
    st.info("No observations are available for this station.")
    footer()
    st.stop()

warmest = station_daily.dropna(subset=["max_temp_c"])
warmest_value = warmest["max_temp_c"].max() if not warmest.empty else float("nan")
facts = st.columns(4)
facts[0].metric("Region", station["region"])
facts[1].metric("Elevation", f"{station['elevation_m']:.0f} m")
facts[2].metric("Annual rainfall", f"{station_daily['rainfall_mm'].sum():,.1f} mm")
facts[3].metric("Warmest day", f"{warmest_value:.1f} °C")
st.caption(
    f"Location: {station['lat']:.3f}, {station['lon']:.3f} · "
    f"Records: {station_daily['date'].min():%d/%m/%Y} to {station_daily['date'].max():%d/%m/%Y}"
)

st.subheader("Daily weather")
st.plotly_chart(station_weather_chart(station_daily), use_container_width=True)

st.subheader("Cumulative growing degree days")
gdd = calc_gdd(station_daily, config.thresholds.gdd_base_c)
st.plotly_chart(gdd_chart(gdd), use_container_width=True)

st.subheader("Monthly summary")
summary = station_monthly_summary(
    station_daily,
    config.thresholds.frost_c,
    config.thresholds.heat_c,
)
st.dataframe(
    summary,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Month": st.column_config.DateColumn("Month", format="MMM YYYY"),
        "Rainfall (mm)": st.column_config.NumberColumn(format="%.1f mm"),
        "Mean max (°C)": st.column_config.NumberColumn(format="%.1f °C"),
        "Mean min (°C)": st.column_config.NumberColumn(format="%.1f °C"),
    },
)

footer()