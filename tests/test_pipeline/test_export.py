"""Tests for pipeline.export — JSON export for frontend."""

import json

import pytest

from pipeline.export import export_for_frontend


class TestExportCreatesFiles:
    """Verify that export produces all expected JSON files."""

    def test_creates_summary_json(self, pipeline_results, export_dir):
        export_for_frontend(pipeline_results, output_dir=export_dir)
        assert (export_dir / "summary.json").exists()

    def test_creates_timeseries_json(self, pipeline_results, export_dir):
        export_for_frontend(pipeline_results, output_dir=export_dir)
        assert (export_dir / "timeseries.json").exists()

    def test_creates_spatial_json(self, pipeline_results, export_dir):
        export_for_frontend(pipeline_results, output_dir=export_dir)
        assert (export_dir / "spatial.json").exists()

    def test_creates_states_json(self, pipeline_results, export_dir):
        export_for_frontend(pipeline_results, output_dir=export_dir)
        assert (export_dir / "states.json").exists()

    def test_creates_counties_json(self, pipeline_results, export_dir):
        export_for_frontend(pipeline_results, output_dir=export_dir)
        assert (export_dir / "counties.json").exists()


class TestExportValidJson:
    """Verify each exported file is parseable JSON."""

    @pytest.fixture(autouse=True)
    def _export(self, pipeline_results, export_dir):
        export_for_frontend(pipeline_results, output_dir=export_dir)
        self.export_dir = export_dir

    @pytest.mark.parametrize("filename", [
        "summary.json", "timeseries.json", "spatial.json",
        "states.json", "counties.json",
    ])
    def test_valid_json(self, filename):
        path = self.export_dir / filename
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, dict)


class TestSummaryJsonKeys:
    """Verify summary.json has the expected top-level structure."""

    @pytest.fixture(autouse=True)
    def _export(self, pipeline_results, export_dir):
        export_for_frontend(pipeline_results, output_dir=export_dir)
        with open(export_dir / "summary.json") as f:
            self.data = json.load(f)

    def test_has_metadata(self):
        assert "metadata" in self.data

    def test_has_headline(self):
        assert "headline" in self.data

    def test_headline_keys(self):
        expected = {
            "total_population", "population_affected", "population_severe",
            "pct_affected", "pct_severe", "tws_trend_cm_per_year",
            "precip_trend_mm_per_year",
        }
        assert expected <= set(self.data["headline"].keys())


class TestTimeseriesJsonKeys:
    """Verify timeseries.json has expected arrays."""

    @pytest.fixture(autouse=True)
    def _export(self, pipeline_results, export_dir):
        export_for_frontend(pipeline_results, output_dir=export_dir)
        with open(export_dir / "timeseries.json") as f:
            self.data = json.load(f)

    def test_has_dates(self):
        assert "dates" in self.data
        assert len(self.data["dates"]) > 0

    def test_has_tws_monthly(self):
        assert "tws_monthly" in self.data
        assert len(self.data["tws_monthly"]) == len(self.data["dates"])

    def test_has_precip_monthly(self):
        assert "precip_monthly" in self.data
        assert len(self.data["precip_monthly"]) == len(self.data["dates"])

    def test_values_are_rounded(self):
        # TWS monthly values should be rounded to 2 decimal places
        for v in self.data["tws_monthly"]:
            assert v == round(v, 2)


class TestSpatialJsonKeys:
    """Verify spatial.json has expected grid data."""

    @pytest.fixture(autouse=True)
    def _export(self, pipeline_results, export_dir):
        export_for_frontend(pipeline_results, output_dir=export_dir)
        with open(export_dir / "spatial.json") as f:
            self.data = json.load(f)

    def test_has_lat_lon(self):
        assert "lat" in self.data
        assert "lon" in self.data

    def test_has_tws_trend(self):
        assert "tws_trend" in self.data
        assert len(self.data["tws_trend"]) == len(self.data["lat"])

    def test_has_precip_change(self):
        assert "precip_change" in self.data


class TestStatesJsonKeys:
    """Verify states.json has expected per-state data."""

    @pytest.fixture(autouse=True)
    def _export(self, pipeline_results, export_dir):
        export_for_frontend(pipeline_results, output_dir=export_dir)
        with open(export_dir / "states.json") as f:
            self.data = json.load(f)

    def test_has_dates_and_states(self):
        assert "dates" in self.data
        assert "states" in self.data

    def test_state_has_required_fields(self):
        for state, info in self.data["states"].items():
            assert "population" in info
            assert "tws_trend" in info
            assert "water_stress" in info
            assert "tws_timeseries" in info
