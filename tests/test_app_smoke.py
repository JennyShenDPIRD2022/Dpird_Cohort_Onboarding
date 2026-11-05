"""Smoke tests for both Streamlit entry points."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from weather.config import ROOT, load_config

CONFIG = load_config()
DATA_AVAILABLE = CONFIG.paths.stations.exists() and CONFIG.paths.daily_weather.exists()


@pytest.mark.skipif(not DATA_AVAILABLE, reason="Generate data before running app smoke tests")
@pytest.mark.parametrize("entry_point", [ROOT / "Overview.py", ROOT / "pages/1_Station_detail.py"])
def test_streamlit_page_starts_without_exceptions(entry_point: Path) -> None:
    app = AppTest.from_file(str(entry_point)).run(timeout=30)

    assert not app.exception