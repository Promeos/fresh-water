"""Tests for pipeline.fetch_grace — GRACE TWS anomaly data."""

import numpy as np
import pytest

from pipeline.config import REGION


class TestGraceDataStructure:
    """Verify load_grace_data returns the expected dict structure."""

    def test_has_required_keys(self, grace_data):
        required = {"lat", "lon", "time_months_since_200204", "tws_anomaly_cm"}
        assert required <= set(grace_data.keys())

    def test_lat_is_list(self, grace_data):
        assert isinstance(grace_data["lat"], list)
        assert len(grace_data["lat"]) > 0

    def test_lon_is_list(self, grace_data):
        assert isinstance(grace_data["lon"], list)
        assert len(grace_data["lon"]) > 0

    def test_time_is_list(self, grace_data):
        assert isinstance(grace_data["time_months_since_200204"], list)
        assert len(grace_data["time_months_since_200204"]) > 0


class TestGraceGrid:
    """Verify grid dimensions match the region config."""

    def test_lat_within_region(self, grace_data):
        lats = grace_data["lat"]
        assert min(lats) >= REGION["min_lat"] - 0.5
        assert max(lats) <= REGION["max_lat"] + 0.5

    def test_lon_within_region(self, grace_data):
        lons = grace_data["lon"]
        assert min(lons) >= REGION["min_lon"] - 0.5
        assert max(lons) <= REGION["max_lon"] + 0.5

    def test_tws_shape_matches_grid(self, grace_data):
        tws = np.array(grace_data["tws_anomaly_cm"])
        n_time = len(grace_data["time_months_since_200204"])
        n_lat = len(grace_data["lat"])
        n_lon = len(grace_data["lon"])
        assert tws.shape == (n_time, n_lat, n_lon)


class TestGraceValues:
    """Verify TWS anomaly values are reasonable."""

    def test_no_nan(self, grace_data):
        tws = np.array(grace_data["tws_anomaly_cm"])
        assert not np.any(np.isnan(tws)), "TWS data contains NaN values"

    def test_no_inf(self, grace_data):
        tws = np.array(grace_data["tws_anomaly_cm"])
        assert not np.any(np.isinf(tws)), "TWS data contains Inf values"

    def test_range_reasonable(self, grace_data):
        tws = np.array(grace_data["tws_anomaly_cm"])
        # Synthetic data with drought pulses can produce large anomalies
        assert tws.min() > -150, f"Min TWS {tws.min()} below -150 cm"
        assert tws.max() < 150, f"Max TWS {tws.max()} above 150 cm"

    def test_time_monotonic(self, grace_data):
        times = grace_data["time_months_since_200204"]
        assert all(
            times[i] <= times[i + 1] for i in range(len(times) - 1)
        ), "Time values are not monotonically increasing"
