"""Plotly figure builders with a shared visual language."""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

COLORS = {
    "rain": "#58A6FF",
    "max_temp": "#F85149",
    "min_temp": "#79C0FF",
    "heat_event": "#D29922",
    "frost_event": "#A371F7",
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


def station_weather_chart(
    df: pd.DataFrame, *, heat_threshold_c: float, frost_threshold_c: float
) -> go.Figure:
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
    heat_days = df.dropna(subset=["max_temp_c"]).loc[
        lambda data: data["max_temp_c"] >= heat_threshold_c
    ]
    frost_nights = df.dropna(subset=["min_temp_c"]).loc[
        lambda data: data["min_temp_c"] < frost_threshold_c
    ]
    figure.add_scatter(
        x=heat_days["date"],
        y=heat_days["max_temp_c"],
        name="Heat day",
        mode="markers",
        marker={"color": COLORS["heat_event"], "symbol": "triangle-up", "size": 11},
        hovertemplate=(
            "%{x|%d/%m/%Y}<br>Temperature: %{y:.1f} °C<br>Event: Heat day<extra></extra>"
        ),
        secondary_y=True,
    )
    figure.add_scatter(
        x=frost_nights["date"],
        y=frost_nights["min_temp_c"],
        name="Frost night",
        mode="markers",
        marker={"color": COLORS["frost_event"], "symbol": "triangle-down", "size": 11},
        hovertemplate=(
            "%{x|%d/%m/%Y}<br>Temperature: %{y:.1f} °C<br>Event: Frost night<extra></extra>"
        ),
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


def rainfall_station_totals_chart(summary: pd.DataFrame) -> go.Figure:
    """Build ranked bars from the ordered station summary, keeping unknown totals distinct."""
    figure = go.Figure(go.Bar(
        x=summary["Observed rainfall (mm)"],
        y=summary["Station"],
        orientation="h",
        marker_color=COLORS["rain"],
        customdata=summary[["Observed days", "Days in selection", "Coverage (%)"]],
        hovertemplate=(
            "%{y}<br>Observed rainfall: %{x:.1f} mm<br>"
            "Observed days: %{customdata[0]} / %{customdata[1]}<br>"
            "Coverage: %{customdata[2]:.1f}%<extra></extra>"
        ),
    ))
    for _, row in summary.iterrows():
        total = row["Observed rainfall (mm)"]
        if pd.isna(total) or total == 0:
            figure.add_annotation(
                x=0,
                y=row["Station"],
                text="No observations" if pd.isna(total) else "0.0 mm",
                showarrow=False,
                xanchor="left",
                xshift=6,
            )
    figure.update_xaxes(title="Observed rainfall (mm)", rangemode="tozero")
    figure.update_yaxes(
        title="Station",
        type="category",
        categoryorder="array",
        categoryarray=summary["Station"].tolist(),
        autorange="reversed",
        automargin=True,
    )
    _style(figure, height=max(320, 32 * len(summary) + 100))
    figure.update_layout(showlegend=False, hovermode="closest")
    return figure


def rainfall_comparison_chart(df: pd.DataFrame, *, cumulative: bool = False) -> go.Figure:
    """Compare period totals or cumulative observed rainfall without connecting missing periods."""
    figure = go.Figure()
    value = "cumulative_rainfall_mm" if cumulative else "rainfall_mm"
    label = "Cumulative observed rainfall (mm)" if cumulative else "Observed rainfall (mm)"
    for station, station_data in df.groupby("station", sort=True):
        figure.add_scatter(
            x=station_data["period"],
            y=station_data[value],
            name=station,
            mode="lines+markers",
            connectgaps=False,
            customdata=station_data[["observed_days", "expected_days"]],
            hovertemplate=(
                f"%{{x|%d/%m/%Y}}<br>{label}: %{{y:.1f}}<br>"
                "Observed days in period: %{customdata[0]} / %{customdata[1]}<extra>%{fullData.name}</extra>"
            ),
        )
    figure.update_yaxes(title=label, rangemode="tozero")
    figure.update_xaxes(title="Period start", type="date")
    figure.update_layout(colorway=[
        COLORS["rain"], COLORS["accent"], COLORS["gdd"], COLORS["heat_event"],
        COLORS["max_temp"], COLORS["min_temp"], "#F778BA", "#FFA657",
        "#A5D6FF", "#7EE787", "#D2A8FF", "#FFDCD7",
    ])
    return _style(figure, height=460)


def rainfall_heatmap_chart(df: pd.DataFrame) -> go.Figure:
    """Show monthly station totals with blank cells for unobserved months."""
    totals = df.pivot(index="station", columns="period", values="rainfall_mm").sort_index()
    observed = df.pivot(index="station", columns="period", values="observed_days").reindex_like(totals)
    expected = df.pivot(index="station", columns="period", values="expected_days").reindex_like(totals)
    coverage = observed.astype(str) + " / " + expected.astype(str)
    figure = go.Figure(go.Heatmap(
        x=totals.columns,
        y=totals.index,
        z=totals.to_numpy(),
        customdata=coverage.to_numpy(),
        colorscale=[[0, "#162A40"], [1, COLORS["rain"]]],
        zmin=0,
        colorbar={"title": "Rainfall (mm)"},
        hoverongaps=False,
        hovertemplate=(
            "%{y}<br>%{x|%b %Y}<br>Observed rainfall: %{z:.1f} mm<br>"
            "Observed days: %{customdata}<extra></extra>"
        ),
    ))
    figure.update_xaxes(title="Month", tickformat="%b %Y", type="date")
    figure.update_yaxes(title="Station", autorange="reversed")
    _style(figure, height=max(360, 30 * len(totals) + 120))
    figure.update_layout(hovermode="closest")
    return figure