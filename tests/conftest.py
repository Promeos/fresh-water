"""Shared fixtures for the Fresh Water Monitor test suite."""

import json
import shutil
from pathlib import Path

import numpy as np
import pytest

from pipeline.config import RAW_DIR


# ---------------------------------------------------------------------------
# Helpers: ensure synthetic data files exist before tests that need them
# ---------------------------------------------------------------------------

def _ensure_raw_data():
    """Generate synthetic raw data if it does not already exist."""
    from pipeline.fetch_grace import fetch_grace_data
    from pipeline.fetch_gpm import fetch_gpm_data
    from pipeline.fetch_population import generate_population_data

    fetch_grace_data()
    fetch_gpm_data()
    generate_population_data()


# ---------------------------------------------------------------------------
# Session-scoped fixtures (expensive — run once per test session)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def grace_data():
    """Load GRACE data (generates synthetic if needed)."""
    _ensure_raw_data()
    from pipeline.fetch_grace import load_grace_data
    return load_grace_data()


@pytest.fixture(scope="session")
def gpm_data():
    """Load GPM data (generates synthetic if needed)."""
    _ensure_raw_data()
    from pipeline.fetch_gpm import load_gpm_data
    return load_gpm_data()


@pytest.fixture(scope="session")
def pop_data():
    """Load population data (generates synthetic if needed)."""
    _ensure_raw_data()
    from pipeline.fetch_population import load_population_data
    return load_population_data()


@pytest.fixture(scope="session")
def pipeline_results(grace_data, gpm_data, pop_data):
    """Run the full processing pipeline once per session."""
    from pipeline.process import run_pipeline
    return run_pipeline()


@pytest.fixture()
def export_dir(tmp_path):
    """Provide a temporary directory for JSON export tests."""
    return tmp_path / "export"
