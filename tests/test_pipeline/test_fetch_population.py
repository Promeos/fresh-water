"""Tests for pipeline.fetch_population — population data."""

import numpy as np
import pytest

from pipeline.config import STATES


class TestPopDataStructure:
    """Verify load_population_data returns the expected dict structure."""

    def test_has_required_keys(self, pop_data):
        required = {
            "lat", "lon", "years", "gridded_population",
            "state_summary", "total_population_2023",
        }
        assert required <= set(pop_data.keys())

    def test_years_list(self, pop_data):
        assert isinstance(pop_data["years"], list)
        assert len(pop_data["years"]) > 0

    def test_gridded_population_is_dict(self, pop_data):
        assert isinstance(pop_data["gridded_population"], dict)


class TestPopValues:
    """Verify population values are realistic."""

    def test_total_population_reasonable(self, pop_data):
        total = pop_data["total_population_2023"]
        # US population should be between 300M and 400M
        assert 300_000_000 < total < 400_000_000, (
            f"Total population {total:,} is not in expected range"
        )

    def test_gridded_population_positive(self, pop_data):
        grid_2023 = np.array(pop_data["gridded_population"]["2023"])
        # Grid values should be non-negative (some cells may be near-zero)
        assert np.all(grid_2023 >= 0), "Population grid contains negative values"

    def test_gridded_sum_matches_total(self, pop_data):
        grid_2023 = np.array(pop_data["gridded_population"]["2023"])
        grid_total = grid_2023.sum()
        expected = pop_data["total_population_2023"]
        # Gaussian kernel spread means totals may not match exactly,
        # but should be within 5%
        assert abs(grid_total - expected) / expected < 0.05


class TestPopStateSummary:
    """Verify state_summary covers all 50 states."""

    def test_all_50_states_present(self, pop_data):
        summary = pop_data["state_summary"]
        for state in STATES:
            assert state in summary, f"Missing state: {state}"

    def test_state_population_positive(self, pop_data):
        for state, info in pop_data["state_summary"].items():
            assert info["population_2023"] > 0, f"{state} has non-positive population"

    def test_state_has_coordinates(self, pop_data):
        for state, info in pop_data["state_summary"].items():
            assert "center_lat" in info, f"{state} missing center_lat"
            assert "center_lon" in info, f"{state} missing center_lon"

    def test_state_has_growth_rate(self, pop_data):
        for state, info in pop_data["state_summary"].items():
            assert "annual_growth_pct" in info, f"{state} missing growth rate"
