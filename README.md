# WA Weather Tracker

WA Weather Tracker is a small Streamlit app for exploring rainfall, maximum and minimum
temperature, frost, heat and growing conditions across 12 Western Australian weather
stations during 2024.

> **All observations in this project are synthetic and intended for demonstration only.**
> They must not be used for forecasting, safety decisions or historical analysis.

## Features

- Region and date filters with headline weather metrics
- Monthly rainfall and daily temperature charts
- A token-free station map sized by rainfall
- Station-level weather, growing degree days and monthly summaries
- Deliberate data-quality issues to demonstrate cleaning workflows

Configuration in `config.yaml` controls every data path and weather threshold.

## Quick start

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python scripts/generate_data.py
streamlit run Overview.py
```

Run the tests and linter:

```powershell
ruff check .
pytest
```

### macOS and Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/generate_data.py
streamlit run Overview.py
```

Run the tests and linter:

```bash
ruff check .
pytest
```

The app opens at `http://localhost:8501`. Generated CSV files are written to `data/`
and are intentionally excluded from Git.

## Project structure

```text
.
├── Overview.py                    # Overview page
├── pages/1_Station_detail.py      # Station analysis page
├── weather/                       # Data, metrics, charts and app logic
├── scripts/generate_data.py       # Deterministic synthetic data generator
├── legacy/station_rankings.R      # Base-R monthly station ranking
├── tests/                         # Metrics, charts and app smoke tests
├── config.yaml                    # Paths and weather thresholds
└── .github/workflows/ci.yml       # Python 3.12 CI
```