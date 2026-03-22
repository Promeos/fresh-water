"""Tests for pipeline.fetch_gpm — GPM IMERG precipitation data."""

import numpy as np
import pytest

from pipeline.config import REGION


class TestGpmDataStructure:
    """Verify load_gpm_data returns the expected dict structure."""

    def test_has_required_keys(self, gpm_data):
        required = {"lat", "lon", "time_months_since_200204", "precipitation_mm"}
        assert required <= set(gpm_data.keys())

    def test_lat_is_list(self, gpm_data):
        assert isinstance(gpm_data["lat"], list)
        assert len(gpm_data["lat"]) > 0

    def test_lon_is_list(self, gpm_data):
        assert isinstance(gpm_data["lon"], list)
        assert len(gpm_data["lon"]) > 0

    def test_time_is_list(self, gpm_data):
        assert isinstance(gpm_data["time_months_since_200204"], list)
        assert len(gpm_data["time_months_since_200204"]) > 0


class TestGpmGrid:
    """Verify grid dimensions and spatial bounds."""

    def test_lat_within_region(self, gpm_data):
        lats = gpm_data["lat"]
        assert min(lats) >= REGION["min_lat"] - 0.5
        assert max(lats) <= REGION["max_lat"] + 0.5

    def test_lon_within_region(self, gpm_data):
        lons = gpm_data["lon"]
        assert min(lons) >= REGION["min_lon"] - 0.5
        assert max(lons) <= REGION["max_lon"] + 0.5

    def test_precip_shape_matches_grid(self, gpm_data):
        precip = np.array(gpm_data["precipitation_mm"])
        n_time = len(gpm_data["time_months_since_200204"])
        n_lat = len(gpm_data["lat"])
        n_lon = len(gpm_data["lon"])
        assert precip.shape == (n_time, n_lat, n_lon)


class TestGpmValues:
    """Verify precipitation values are physically reasonable."""

    def test_non_negative(self, gpm_data):
        precip = np.array(gpm_data["precipitation_mm"])
        assert np.all(precip >= 0), "Precipitation contains negative values"

    def test_no_nan(self, gpm_data):
        precip = np.array(gpm_data["precipitation_mm"])
        assert not np.any(np.isnan(precip)), "Precipitation contains NaN values"

    def test_no_inf(self, gpm_data):
        precip = np.array(gpm_data["precipitation_mm"])
        assert not np.any(np.isinf(precip)), "Precipitation contains Inf values"

    def test_reasonable_max(self, gpm_data):
        precip = np.array(gpm_data["precipitation_mm"])
        # 2000 mm/month is an extreme upper bound (some tropical regions can exceed 1000)
        assert precip.max() < 2000, f"Max precip {precip.max()} exceeds 2000 mm/month"


class TestGpmTimeAlignment:
    """Verify GPM and GRACE time axes are compatible."""

    def test_time_overlap_with_grace(self, gpm_data, grace_data):
        """GPM and GRACE should have substantial temporal overlap.

        They may not have identical month counts (GPM starts Jun 2000,
        GRACE starts Apr 2002), but both should cover multiple years.
        The pipeline aligns them during processing.
        """
        gpm_months = len(gpm_data["time_months_since_200204"])
        grace_months = len(grace_data["time_months_since_200204"])
        # Both should have at least 100 months of data
        assert gpm_months > 100
        assert grace_months > 100
