"""Focused tests for Plotly chart builders."""

import pandas as pd
import pytest

from weather.charts import (
    COLORS,
    gdd_chart,
    monthly_rainfall_chart,
    rainfall_comparison_chart,
    rainfall_heatmap_chart,
    rainfall_station_totals_chart,
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


@pytest.mark.parametrize("cumulative", [False, True])
def test_rainfall_comparison_keeps_gaps_and_exposes_coverage(cumulative: bool) -> None:
    data = pd.DataFrame({
        "station": ["Alpha"] * 3,
        "period": pd.date_range("2024-01-01", periods=3),
        "rainfall_mm": [2.0, None, 0.0],
        "cumulative_rainfall_mm": [2.0, None, 2.0],
        "observed_days": [1, 0, 1],
        "expected_days": [1, 1, 1],
    })

    figure = rainfall_comparison_chart(data, cumulative=cumulative)

    assert figure.data[0].type == "scatter"
    assert figure.data[0].connectgaps is False
    assert pd.isna(figure.data[0].y[1])
    assert figure.data[0].y[2] == (2.0 if cumulative else 0.0)
    assert list(figure.data[0].customdata[1]) == [0, 1]
    assert "Observed days in period" in figure.data[0].hovertemplate
    assert figure.layout.paper_bgcolor == "rgba(0,0,0,0)"
    assert figure.layout.xaxis.title.text == "Period start"
    assert figure.layout.yaxis.title.text == (
        "Cumulative observed rainfall (mm)" if cumulative else "Observed rainfall (mm)"
    )


def test_rainfall_heatmap_distinguishes_zero_and_missing() -> None:
    data = pd.DataFrame({
        "station": ["Beta", "Beta", "Alpha", "Alpha"],
        "period": pd.to_datetime(["2024-02-01", "2024-01-01"] * 2),
        "rainfall_mm": [None, None, 0.0, 4.0],
        "observed_days": [0, 0, 29, 30],
        "expected_days": [29, 31, 29, 31],
    })

    figure = rainfall_heatmap_chart(data)
    heatmap = figure.data[0]

    assert heatmap.type == "heatmap"
    assert list(heatmap.y) == ["Alpha", "Beta"]
    assert list(heatmap.z[0]) == [4.0, 0.0]
    assert pd.isna(heatmap.z[1]).all()
    assert heatmap.customdata[0][0] == "30 / 31"
    assert heatmap.hoverongaps is False
    assert heatmap.zmin == 0
    assert figure.layout.hovermode == "closest"
    assert figure.layout.paper_bgcolor == "rgba(0,0,0,0)"


def test_station_totals_chart_preserves_ranking_zero_and_missing() -> None:
    summary = pd.DataFrame({
        "Station": ["Wet", "Partial", "Dry", "Missing"],
        "Observed rainfall (mm)": [40.0, 10.0, 0.0, None],
        "Observed days": [4, 2, 4, 0],
        "Days in selection": [4] * 4,
        "Coverage (%)": [100.0, 50.0, 100.0, 0.0],
    })

    figure = rainfall_station_totals_chart(summary)
    bars = figure.data[0]

    assert bars.type == "bar"
    assert bars.orientation == "h"
    assert bars.marker.color == COLORS["rain"]
    assert list(bars.y) == ["Wet", "Partial", "Dry", "Missing"]
    assert list(bars.x[:3]) == [40.0, 10.0, 0.0]
    assert pd.isna(bars.x[3])
    assert list(bars.customdata[1]) == [2, 4, 50]
    assert "Coverage: %{customdata[2]:.1f}%" in bars.hovertemplate
    assert [(label.y, label.text) for label in figure.layout.annotations] == [
        ("Dry", "0.0 mm"), ("Missing", "No observations"),
    ]
    assert list(figure.layout.yaxis.categoryarray) == list(bars.y)
    assert figure.layout.yaxis.autorange == "reversed"
    assert figure.layout.xaxis.title.text == "Observed rainfall (mm)"
    assert figure.layout.hovermode == "closest"
    assert figure.layout.paper_bgcolor == "rgba(0,0,0,0)"


@pytest.mark.parametrize("total", [0.0, float("nan")])
def test_station_totals_chart_handles_single_station_without_a_bar(total: float) -> None:
    summary = pd.DataFrame({
        "Station": ["Alpha"],
        "Observed rainfall (mm)": [total],
        "Observed days": [0 if pd.isna(total) else 1],
        "Days in selection": [1],
        "Coverage (%)": [0 if pd.isna(total) else 100],
    })

    figure = rainfall_station_totals_chart(summary)

    assert list(figure.data[0].y) == ["Alpha"]
    assert figure.layout.annotations[0].text == ("No observations" if pd.isna(total) else "0.0 mm")