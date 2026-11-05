"""Rainfall comparison, missing-data and interactive page tests."""

import json
from datetime import date

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from weather.app_logic import rainfall_comparison_days, rainfall_station_summary
from weather.config import ROOT
from weather.metrics import rainfall_period_totals


@pytest.fixture
def observations() -> pd.DataFrame:
    return pd.DataFrame({
        "station": ["Alpha", "Alpha", "Alpha", "Alpha", "Beta", "Beta", "Beta", "Beta", "Other"],
        "date": pd.to_datetime([
            "2024-01-29", "2024-01-30", "2024-01-31", "2024-02-02",
            "2024-01-30", "2024-01-31", "2024-02-01", "2024-02-02", "2024-01-30",
        ]),
        "rainfall_mm": [99.0, 0.0, None, 5.0, 2.0, 3.0, None, 0.0, 100.0],
    })


@pytest.fixture
def comparison(observations: pd.DataFrame) -> pd.DataFrame:
    return rainfall_comparison_days(
        observations, ["Gamma", "Beta", "Alpha"], date(2024, 1, 30), date(2024, 2, 2),
    )


def test_daily_grid_filters_inclusively_and_preserves_missing_rows(observations: pd.DataFrame) -> None:
    original = observations.copy(deep=True)
    result = rainfall_comparison_days(observations, ["Alpha", "Gamma"], date(2024, 1, 30), date(2024, 2, 2))

    assert len(result) == 8
    assert result["station"].unique().tolist() == ["Alpha", "Gamma"]
    alpha = result.loc[result["station"] == "Alpha", "rainfall_mm"].reset_index(drop=True)
    pd.testing.assert_series_equal(alpha, pd.Series([0.0, None, None, 5.0], name="rainfall_mm"))
    assert result.loc[result["station"] == "Gamma", "rainfall_mm"].isna().all()
    pd.testing.assert_frame_equal(observations, original)


def test_monthly_totals_use_selected_days_and_keep_all_missing_unknown(comparison: pd.DataFrame) -> None:
    result = rainfall_period_totals(comparison, "Monthly").set_index(["station", "period"])

    assert result.loc[("Alpha", "2024-01-01"), "rainfall_mm"] == 0.0
    assert result.loc[("Alpha", "2024-02-01"), "rainfall_mm"] == 5.0
    assert result.loc[("Beta", "2024-01-01"), "rainfall_mm"] == 5.0
    assert result.loc[("Beta", "2024-02-01"), "rainfall_mm"] == 0.0
    assert result.loc["Gamma", "rainfall_mm"].isna().all()
    assert result["expected_days"].tolist() == [2] * 6
    assert result["observed_days"].tolist() == [1, 1, 2, 1, 0, 0]


def test_daily_cumulative_resumes_observed_sum_after_gaps(comparison: pd.DataFrame) -> None:
    result = rainfall_period_totals(comparison, "Daily")
    alpha = result.loc[result["station"] == "Alpha", "cumulative_rainfall_mm"].reset_index(drop=True)

    pd.testing.assert_series_equal(alpha, pd.Series([0.0, None, None, 5.0], name="cumulative_rainfall_mm"))
    assert result.loc[result["station"] == "Beta", "cumulative_rainfall_mm"].dropna().tolist() == [2, 5, 5]
    assert result.loc[result["station"] == "Gamma", "cumulative_rainfall_mm"].isna().all()


def test_weekly_totals_start_monday_and_count_partial_weeks() -> None:
    daily = pd.DataFrame({
        "station": ["Alpha"] * 9,
        "date": pd.date_range("2024-01-28", "2024-02-05"),
        "rainfall_mm": [1.0] * 9,
    })

    result = rainfall_period_totals(daily.sample(frac=1, random_state=0), "Weekly")

    assert result["period"].dt.strftime("%Y-%m-%d").tolist() == ["2024-01-22", "2024-01-29", "2024-02-05"]
    assert result["rainfall_mm"].tolist() == [1, 7, 1]
    assert result["expected_days"].tolist() == [1, 7, 1]
    assert result["cumulative_rainfall_mm"].tolist() == [1, 8, 9]


def test_summary_distinguishes_dry_missing_and_partial_coverage(comparison: pd.DataFrame) -> None:
    result = rainfall_station_summary(comparison).set_index("Station")

    assert result.index.tolist() == ["Alpha", "Beta", "Gamma"]
    assert result.loc["Alpha", "Observed rainfall (mm)"] == 5
    assert result.loc["Alpha", "Wettest day (mm)"] == 5
    assert result.loc["Alpha", "Rain days (>0 mm)"] == 1
    assert result["Observed days"].tolist() == [2, 3, 0]
    assert result["Days in selection"].tolist() == [4, 4, 4]
    assert result["Coverage (%)"].tolist() == [50, 75, 0]
    assert result.loc["Gamma", ["Observed rainfall (mm)", "Wettest day (mm)", "Rain days (>0 mm)"]].isna().all()
    dry = rainfall_station_summary(comparison.loc[comparison["date"] == pd.Timestamp("2024-01-30")])
    assert dry.set_index("Station").loc["Alpha", "Rain days (>0 mm)"] == 0


def test_leap_day_single_day_and_empty_selections(observations: pd.DataFrame) -> None:
    leap = rainfall_comparison_days(observations, ["Alpha"], date(2024, 2, 1), date(2024, 2, 29))
    assert len(leap) == 29
    assert rainfall_period_totals(leap, "Monthly").iloc[0]["expected_days"] == 29
    single = rainfall_comparison_days(observations, ["Alpha"], date(2024, 2, 2), date(2024, 2, 2))
    assert rainfall_station_summary(single).iloc[0]["Coverage (%)"] == 100
    empty = rainfall_comparison_days(observations, [], date(2024, 1, 1), date(2024, 1, 1))
    assert rainfall_station_summary(empty).empty
    assert rainfall_period_totals(empty, "Monthly").empty
    with pytest.raises(ValueError, match="end date"):
        rainfall_comparison_days(observations, ["Alpha"], date(2024, 2, 2), date(2024, 2, 1))


@pytest.fixture
def explorer(monkeypatch: pytest.MonkeyPatch, observations: pd.DataFrame) -> AppTest:
    metadata = pd.DataFrame({"station": ["Alpha", "Beta", "Gamma"], "region": ["North", "South", "North"]})
    monkeypatch.setattr("weather.data.load_daily", lambda: observations)
    monkeypatch.setattr("weather.data.load_stations", lambda: metadata)
    return AppTest.from_file(str(ROOT / "pages/2_Rainfall_explorer.py")).run(timeout=30)


def test_explorer_filters_dates_stations_and_view(explorer: AppTest) -> None:
    assert not explorer.exception
    assert len(explorer.get("plotly_chart")) == 3
    ranked = json.loads(explorer.get("plotly_chart")[0].proto.spec)
    assert ranked["data"][0]["type"] == "bar"
    assert ranked["data"][0]["y"] == ["Alpha", "Beta", "Gamma"]
    explorer.sidebar.date_input[0].set_value((date(2024, 1, 30), date(2024, 2, 2)))
    explorer.sidebar.multiselect[1].set_value(["Alpha", "Beta"])
    explorer.sidebar.selectbox[0].set_value("Weekly")
    explorer.run()
    explorer.radio[0].set_value("Cumulative observed rainfall").run()

    assert not explorer.exception
    assert [metric.value for metric in explorer.metric] == ["2", "4", "62.5%"]
    assert explorer.dataframe[0].value["Observed rainfall (mm)"].tolist() == [5, 5]
    ranked = json.loads(explorer.get("plotly_chart")[0].proto.spec)
    assert ranked["data"][0]["y"] == ["Alpha", "Beta"]
    assert not ranked["layout"].get("annotations")
    assert "3 of 8" in explorer.warning[0].value
    explorer.sidebar.selectbox[0].set_value("Daily").run()
    assert not explorer.exception
    explorer.sidebar.multiselect[0].set_value(["South"]).run()
    assert not explorer.exception
    assert explorer.sidebar.multiselect[1].options == ["Beta"]
    assert explorer.dataframe[0].value["Station"].tolist() == ["Beta"]
    ranked = json.loads(explorer.get("plotly_chart")[0].proto.spec)
    assert ranked["data"][0]["y"] == ["Beta"]


def test_explorer_ranking_changes_with_selected_dates(explorer: AppTest) -> None:
    explorer.sidebar.date_input[0].set_value((date(2024, 1, 30), date(2024, 1, 30))).run()

    assert not explorer.exception
    ranked = json.loads(explorer.get("plotly_chart")[0].proto.spec)
    assert ranked["data"][0]["y"] == ["Beta", "Alpha", "Gamma"]
    assert [(label["y"], label["text"]) for label in ranked["layout"]["annotations"]] == [
        ("Alpha", "0.0 mm"), ("Gamma", "No observations"),
    ]
    explorer.sidebar.multiselect[1].set_value(["Alpha"]).run()
    assert not explorer.exception
    assert len(explorer.get("plotly_chart")) == 3
    assert explorer.dataframe[0].value["Observed rainfall (mm)"].tolist() == [0]


@pytest.mark.parametrize("selection", ["regions", "stations", "date", "missing"])
def test_explorer_handles_empty_and_missing_selections(explorer: AppTest, selection: str) -> None:
    if selection == "regions":
        explorer.sidebar.multiselect[0].set_value([])
    elif selection == "stations":
        explorer.sidebar.multiselect[1].set_value([])
    elif selection == "date":
        explorer.sidebar.date_input[0].set_value((date(2024, 1, 30),))
    else:
        explorer.sidebar.multiselect[1].set_value(["Gamma"])
    explorer.run()

    assert not explorer.exception
    assert explorer.info
    assert not explorer.get("plotly_chart")
    if selection == "missing":
        assert explorer.metric[2].value == "0.0%"
        assert explorer.dataframe[0].value["Observed rainfall (mm)"].isna().all()


def test_explorer_handles_empty_source(monkeypatch: pytest.MonkeyPatch, observations: pd.DataFrame) -> None:
    monkeypatch.setattr("weather.data.load_daily", lambda: observations.iloc[:0])
    monkeypatch.setattr("weather.data.load_stations", lambda: pd.DataFrame())
    app = AppTest.from_file(str(ROOT / "pages/2_Rainfall_explorer.py")).run(timeout=30)
    assert not app.exception
    assert "No observations" in app.info[0].value


def test_explorer_reports_missing_source(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing_data() -> pd.DataFrame:
        raise FileNotFoundError("Missing daily observations")

    monkeypatch.setattr("weather.data.load_daily", missing_data)
    app = AppTest.from_file(str(ROOT / "pages/2_Rainfall_explorer.py")).run(timeout=30)
    assert not app.exception
    assert "Weather data is not available" in app.error[0].value
