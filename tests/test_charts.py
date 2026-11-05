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
    station = station_weather_chart(data, heat_threshold_c=35.0, frost_threshold_c=2.0)

    assert trend.data[0].line.color == COLORS["max_temp"]
    assert trend.data[1].line.color == COLORS["min_temp"]
    assert station.data[0].marker.color == COLORS["rain"]
    assert station.layout.yaxis2.title.text == "Temperature (°C)"


def test_station_weather_chart_marks_heat_and_frost_events() -> None:
    data = pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]
            ),
            "rainfall_mm": [0.0, 0.0, 0.0, 0.0, 0.0],
            "max_temp_c": [35.0, 34.9, None, 10.0, 10.0],
            "min_temp_c": [10.0, 10.0, 1.9, 2.0, None],
        }
    )

    figure = station_weather_chart(data, heat_threshold_c=35.0, frost_threshold_c=2.0)
    heat, frost = figure.data[3:]

    assert heat.name == "Heat day"
    assert heat.marker.color == COLORS["heat_event"]
    assert list(heat.y) == [35.0]
    assert "Temperature: %{y:.1f} °C<br>Event: Heat day" in heat.hovertemplate
    assert frost.name == "Frost night"
    assert frost.marker.color == COLORS["frost_event"]
    assert list(frost.y) == [1.9]
    assert "Temperature: %{y:.1f} °C<br>Event: Frost night" in frost.hovertemplate
    assert "%{x|%d/%m/%Y}" in heat.hovertemplate


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