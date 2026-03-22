"""Tests for pipeline.config — validate configuration constants."""

from pipeline.config import REGION, STATES, START_YEAR, END_YEAR, DATA_DIR, RAW_DIR


class TestRegionBounds:
    """Verify the bounding box covers the contiguous US."""

    def test_lat_range_valid(self):
        assert REGION["min_lat"] < REGION["max_lat"]

    def test_lon_range_valid(self):
        assert REGION["min_lon"] < REGION["max_lon"]

    def test_lat_within_us(self):
        assert REGION["min_lat"] >= 20.0
        assert REGION["max_lat"] <= 55.0

    def test_lon_within_us(self):
        assert REGION["min_lon"] >= -130.0
        assert REGION["max_lon"] <= -60.0


class TestStates:
    """Verify the state list is complete and correct."""

    def test_50_states(self):
        assert len(STATES) == 50

    def test_no_duplicates(self):
        assert len(set(STATES)) == len(STATES)

    def test_includes_key_states(self):
        for state in ["California", "Texas", "New York", "Florida", "Alaska", "Hawaii"]:
            assert state in STATES

    def test_all_strings(self):
        assert all(isinstance(s, str) for s in STATES)


class TestYearRange:
    """Verify the analysis time window is sensible."""

    def test_start_year_is_grace_launch(self):
        assert START_YEAR == 2002

    def test_end_year_recent(self):
        assert END_YEAR >= 2024
        assert END_YEAR <= 2030

    def test_range_positive(self):
        assert END_YEAR > START_YEAR


class TestPaths:
    """Verify project path constants resolve correctly."""

    def test_data_dir_under_docs(self):
        assert "docs" in str(DATA_DIR)

    def test_raw_dir_under_pipeline(self):
        assert "pipeline" in str(RAW_DIR)
