"""Integration test — full pipeline produces all expected JSON outputs."""

import json

import pytest

from pipeline.export import export_for_frontend


class TestFullPipeline:
    """End-to-end test: run_pipeline + export produces valid JSON files."""

    def test_all_json_files_created(self, pipeline_results, export_dir):
        export_for_frontend(pipeline_results, output_dir=export_dir)

        expected_files = [
            "summary.json",
            "timeseries.json",
            "spatial.json",
            "states.json",
            "counties.json",
        ]
        for fname in expected_files:
            path = export_dir / fname
            assert path.exists(), f"Missing output file: {fname}"
            with open(path) as f:
                data = json.load(f)
            assert isinstance(data, dict), f"{fname} did not parse as a dict"

    def test_pipeline_results_has_all_sections(self, pipeline_results):
        assert "metadata" in pipeline_results
        assert "timeseries" in pipeline_results
        assert "spatial" in pipeline_results
        assert "impact" in pipeline_results

    def test_metadata_has_region(self, pipeline_results):
        assert pipeline_results["metadata"]["region"] == "United States"

    def test_metadata_has_date_range(self, pipeline_results):
        dr = pipeline_results["metadata"]["date_range"]
        assert "2002" in dr
        assert " to " in dr

    def test_timeseries_dates_start_in_2002(self, pipeline_results):
        dates = pipeline_results["timeseries"]["dates"]
        assert dates[0].startswith("2002"), f"First date {dates[0]} not in 2002"

    def test_timeseries_has_trends(self, pipeline_results):
        ts = pipeline_results["timeseries"]
        assert "tws_trend_cm_per_year" in ts
        assert "precip_trend_mm_per_year" in ts

    def test_impact_has_population(self, pipeline_results):
        impact = pipeline_results["impact"]
        assert impact["population_total"] > 0
        assert "state_impacts" in impact
        assert len(impact["state_impacts"]) == 50
