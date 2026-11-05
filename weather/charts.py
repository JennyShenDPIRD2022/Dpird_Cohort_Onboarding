"""Plotly figure builders with a shared visual language."""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

COLORS = {
    "rain": "#58A6FF",
    "max_temp": "#F85149",
    "min_temp": "#79C0FF",
    "gdd": "#3FB950",
    "accent": "#8250DF",
    "text": "#E6EDF3",
    "grid": "#30363D",
}


def _style(figure: go.Figure, *, height: int = 410) -> go.Figure:
    """Apply the shared transparent chart layout."""
    figure.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": COLORS["text"], "size": 15},
        margin={"l": 20, "r": 20, "t": 35, "b": 20},
        legend={"orientation": "h", "y": 1.08, "x": 0},
        hovermode="x unified",
    )
    figure.update_xaxes(gridcolor=COLORS["grid"], linecolor=COLORS["grid"])
    figure.update_yaxes(gridcolor=COLORS["grid"], linecolor=COLORS["grid"])
    return figure


def monthly_rainfall_chart(df: pd.DataFrame) -> go.Figure:
    """Build grouped monthly rainfall bars by region."""
    figure = go.Figure()
    for region in df["region"].drop_duplicates():
        region_data = df[df["region"] == region]
        figure.add_bar(x=region_data["month"], y=region_data["rainfall_mm"], name=region)
    figure.update_layout(barmode="group", colorway=[COLORS["rain"], COLORS["accent"], "#D29922"])
    figure.update_yaxes(title="Rainfall (mm)")
    return _style(figure)


def temperature_trend_chart(df: pd.DataFrame) -> go.Figure:
    """Build average daily maximum and minimum temperature lines."""
    figure = go.Figure()
    figure.add_scatter(
        x=df["date"], y=df["max_temp_c"], name="Average max", line={"color": COLORS["max_temp"]}
    )
    figure.add_scatter(
        x=df["date"], y=df["min_temp_c"], name="Average min", line={"color": COLORS["min_temp"]}
    )
    figure.update_yaxes(title="Temperature (°C)")
    return _style(figure)


def station_map_chart(df: pd.DataFrame) -> go.Figure:
    """Build a token-free station map sized by total rainfall."""
    sizes = df["rainfall_mm"].fillna(0).clip(lower=0)
    max_size = max(float(sizes.max()), 1.0)
    figure = go.Figure(
        go.Scattermap(
            lat=df["lat"],
            lon=df["lon"],
            mode="markers",
            text=df["station"],
            customdata=df[["region", "rainfall_mm"]],
            hovertemplate=(
                "<b>%{text}</b><br>%{customdata[0]}<br>"
                "%{customdata[1]:.1f} mm<extra></extra>"
            ),
            marker={
                "color": COLORS["rain"],
                "opacity": 0.8,
                "size": 10 + 32 * sizes / max_size,
            },
        )
    )
    figure.update_layout(
        map={"style": "open-street-map", "center": {"lat": -26.5, "lon": 119.5}, "zoom": 3.2},
        showlegend=False,
        hovermode="closest",
    )
    return _style(figure, height=500)


def station_weather_chart(df: pd.DataFrame) -> go.Figure:
    """Build rainfall bars with maximum and minimum temperature lines."""
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    figure.add_bar(
        x=df["date"], y=df["rainfall_mm"], name="Rainfall", marker_color=COLORS["rain"]
    )
    figure.add_scatter(
        x=df["date"],
        y=df["max_temp_c"],
        name="Max temperature",
        line={"color": COLORS["max_temp"], "width": 2},
        secondary_y=True,
    )
    figure.add_scatter(
        x=df["date"],
        y=df["min_temp_c"],
        name="Min temperature",
        line={"color": COLORS["min_temp"], "width": 2},
        secondary_y=True,
    )
    figure.update_yaxes(title="Rainfall (mm)", secondary_y=False)
    figure.update_yaxes(title="Temperature (°C)", secondary_y=True)
    return _style(figure, height=450)


def gdd_chart(df: pd.DataFrame) -> go.Figure:
    """Build a cumulative growing degree day chart."""
    figure = go.Figure(
        go.Scatter(
            x=df["date"],
            y=df["cumulative_gdd"],
            name="Cumulative GDD",
            fill="tozeroy",
            line={"color": COLORS["gdd"], "width": 3},
            fillcolor="rgba(63,185,80,0.16)",
        )
    )
    figure.update_yaxes(title="Growing degree days (°C days)")
    return _style(figure)