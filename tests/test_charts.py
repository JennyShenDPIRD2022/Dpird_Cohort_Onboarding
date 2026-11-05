"""Focused tests for Plotly chart builders."""

import pandas as pd

from weather.charts import (
    COLORS,
    gdd_chart,
    monthly_rainfall_chart,
    station_map_chart,
    station_weather_chart,
    temperature_trend_chart,
)


def test_monthly_rainfall_uses_shared_transparent_layout() -> None:
    data = pd.DataFrame(
        {
            "month": pd.to_datetime(["2024-01-01", "2024-01-01"]),
            "region": ["Kimberley", "South West"],
            "rainfall_mm": [80.0, 10.0],
        }
    )

    figure = monthly_rainfall_chart(data)

    assert [trace.type for trace in figure.data] == ["bar", "bar"]
    assert figure.layout.paper_bgcolor == "rgba(0,0,0,0)"
    assert figure.layout.font.size >= 15
    assert figure.layout.yaxis.title.text == "Rainfall (mm)"


def test_temperature_and_station_charts_use_metric_colors() -> None:
    data = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
            "rainfall_mm": [0.0, 3.0],
            "max_temp_c": [30.0, 31.0],
            "min_temp_c": [18.0, 19.0],
        }
    )

    trend = temperature_trend_chart(data)
    station = station_weather_chart(data)

    assert trend.data[0].line.color == COLORS["max_temp"]
    assert trend.data[1].line.color == COLORS["min_temp"]
    assert station.data[0].marker.color == COLORS["rain"]
    assert station.layout.yaxis2.title.text == "Temperature (°C)"


def test_gdd_and_map_have_expected_trace_types_and_sizing() -> None:
    gdd_data = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
            "cumulative_gdd": [12.0, 25.0],
        }
    )
    map_data = pd.DataFrame(
        {
            "station": ["Dry", "Wet"],
            "region": ["Wheatbelt", "Kimberley"],
            "lat": [-31.0, -16.0],
            "lon": [118.0, 128.0],
            "rainfall_mm": [10.0, 100.0],
        }
    )

    gdd = gdd_chart(gdd_data)
    station_map = station_map_chart(map_data)

    assert gdd.data[0].line.color == COLORS["gdd"]
    assert station_map.data[0].type == "scattermap"
    assert station_map.data[0].marker.size[1] > station_map.data[0].marker.size[0]
    assert station_map.layout.map.style == "open-street-map"