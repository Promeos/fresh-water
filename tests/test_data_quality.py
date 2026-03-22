"""Data quality checks across all pipeline outputs."""

import json
import re

import numpy as np
import pytest

from pipeline.config import REGION
from pipeline.export import export_for_frontend


class TestTwsQuality:
    """TWS anomaly value quality checks."""

    def test_tws_range(self, grace_data):
        tws = np.array(grace_data["tws_anomaly_cm"])
        # Synthetic data with drought pulses can produce large anomalies
        assert tws.min() > -150, f"TWS min {tws.min()} below -150 cm"
        assert tws.max() < 150, f"TWS max {tws.max()} above 150 cm"

    def test_tws_no_nan(self, grace_data):
        tws = np.array(grace_data["tws_anomaly_cm"])
        assert not np.any(np.isnan(tws))

    def test_tws_no_inf(self, grace_data):
        tws = np.array(grace_data["tws_anomaly_cm"])
        assert not np.any(np.isinf(tws))


class TestPrecipQuality:
    """Precipitation value quality checks."""

    def test_precip_non_negative(self, gpm_data):
        precip = np.array(gpm_data["precipitation_mm"])
        assert np.all(precip >= 0)

    def test_precip_no_nan(self, gpm_data):
        precip = np.array(gpm_data["precipitation_mm"])
        assert not np.any(np.isnan(precip))

    def test_precip_no_inf(self, gpm_data):
        precip = np.array(gpm_data["precipitation_mm"])
        assert not np.any(np.isinf(precip))


class TestPopulationQuality:
    """Population value quality checks."""

    def test_population_positive_integers(self, pop_data):
        for state, info in pop_data["state_summary"].items():
            pop = info["population_2023"]
            assert pop > 0, f"{state} population not positive"
            assert isinstance(pop, int), f"{state} population not integer"

    def test_grid_no_negative(self, pop_data):
        grid = np.array(pop_data["gridded_population"]["2023"])
        assert np.all(grid >= 0)


class TestDateFormat:
    """Verify all dates match YYYY-MM format."""

    def test_pipeline_dates_format(self, pipeline_results):
        dates = pipeline_results["timeseries"]["dates"]
        pattern = re.compile(r"^\d{4}-\d{2}$")
        for d in dates:
            assert pattern.match(d), f"Date '{d}' not in YYYY-MM format"

    def test_month_values_valid(self, pipeline_results):
        dates = pipeline_results["timeseries"]["dates"]
        for d in dates:
            month = int(d.split("-")[1])
            assert 1 <= month <= 12, f"Month {month} out of range in '{d}'"


class TestSpatialBounds:
    """Verify lat/lon in outputs stay within the region bounding box."""

    def test_grace_lat_bounds(self, grace_data):
        lats = grace_data["lat"]
        assert min(lats) >= REGION["min_lat"] - 0.5
        assert max(lats) <= REGION["max_lat"] + 0.5

    def test_grace_lon_bounds(self, grace_data):
        lons = grace_data["lon"]
        assert min(lons) >= REGION["min_lon"] - 0.5
        assert max(lons) <= REGION["max_lon"] + 0.5

    def test_gpm_lat_bounds(self, gpm_data):
        lats = gpm_data["lat"]
        assert min(lats) >= REGION["min_lat"] - 0.5
        assert max(lats) <= REGION["max_lat"] + 0.5

    def test_gpm_lon_bounds(self, gpm_data):
        lons = gpm_data["lon"]
        assert min(lons) >= REGION["min_lon"] - 0.5
        assert max(lons) <= REGION["max_lon"] + 0.5


class TestOutputJsonQuality:
    """Verify exported JSON files contain no NaN or Inf."""

    @pytest.fixture(autouse=True)
    def _export(self, pipeline_results, export_dir):
        export_for_frontend(pipeline_results, output_dir=export_dir)
        self.export_dir = export_dir

    @pytest.mark.parametrize("filename", [
        "summary.json", "timeseries.json", "spatial.json", "states.json",
    ])
    def test_no_nan_or_inf_in_json(self, filename):
        path = self.export_dir / filename
        text = path.read_text()
        assert "NaN" not in text, f"{filename} contains NaN"
        assert "Infinity" not in text, f"{filename} contains Infinity"
        assert "-Infinity" not in text, f"{filename} contains -Infinity"
