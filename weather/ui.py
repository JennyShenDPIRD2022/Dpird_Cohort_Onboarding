"""Shared Streamlit presentation helpers."""

import streamlit as st


def configure_page(title: str) -> None:
    """Configure a wide dark page and shared visual polish."""
    st.set_page_config(page_title=title, page_icon="🌦️", layout="wide")
    st.markdown(
        """
        <style>
        [data-testid="stMetric"] {
            background: #161B22;
            border: 1px solid #30363D;
            border-radius: 8px;
            padding: 18px 20px;
        }
        [data-testid="stMetricLabel"] { color: #8B949E; }
        h1, h2, h3 { letter-spacing: 0; }
        .stPlotlyChart { border-top: 1px solid #30363D; padding-top: 12px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def synthetic_notice() -> None:
    """Display the synthetic-data disclosure."""
    st.caption("Synthetic 2024 observations · Built for demonstration, not forecasting.")


def footer() -> None:
    """Display the required app footer."""
    st.divider()
    st.caption("Synthetic data for demonstration only.")