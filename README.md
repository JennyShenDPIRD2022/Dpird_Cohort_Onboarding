# WA Weather Tracker

Explore rainfall, temperature, frost, heat and growing conditions across 12 Western
Australian weather stations in 2024 with this Streamlit app.

> **All observations in this project are synthetic and intended for demonstration only.**
> They must not be used for forecasting, safety decisions or historical analysis.

## Features

- Filter by region and date to view headline metrics, rainfall and temperature charts.
- Explore a token-free station map sized by rainfall.
- Review station weather, growing degree days and monthly summaries.
- Practise data cleaning with deliberate data-quality issues.

## Quick start

Requires Python 3.12 or newer. Create and activate a virtual environment:

**Windows PowerShell**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Then install dependencies and start the app:

```sh
python -m pip install -r requirements-dev.txt
streamlit run Overview.py
```

Open `http://localhost:8501`. Demo CSVs are included in [`data/`](data/), copied from
the [original template](https://github.com/danielhardej/ghcp-demo-weather-app/tree/b9015aa9c0714179f7a8f87d85352ed3e7488540/data).
Set data paths and weather thresholds in [`config.yaml`](config.yaml).

## Development

To regenerate the synthetic data, run `python scripts/generate_data.py`.
This overwrites the included CSVs; review any changes before committing.

Run the linter and tests:

```sh
ruff check .
pytest
```

## Project structure

```text
.
├── Overview.py                   # Overview page
├── pages/1_Station_detail.py      # Station analysis page
├── weather/                      # Data, metrics, charts and app logic
├── scripts/generate_data.py       # Deterministic synthetic data generator
├── legacy/station_rankings.R      # Base-R monthly station ranking
├── tests/                        # Metrics, charts and app smoke tests
├── config.yaml                   # Paths and weather thresholds
└── .github/workflows/ci.yml       # Python 3.12 CI
```