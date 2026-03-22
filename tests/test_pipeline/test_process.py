"""Tests for pipeline.process — data processing and analysis."""

import numpy as np
import pytest

from pipeline.process import (
    months_since_200204_to_dates,
    compute_regional_timeseries,
    compute_impact_metrics,
)


class TestMonthsSince200204ToDates:
    """Verify date conversion from month offsets."""

    def test_month_zero_is_april_2002(self):
        result = months_since_200204_to_dates([0])
        assert result == ["2002-04"]

    def test_month_one_is_may_2002(self):
        result = months_since_200204_to_dates([1])
        assert result == ["2002-05"]

    def test_month_eight_is_december_2002(self):
        result = months_since_200204_to_dates([8])
        assert result == ["2002-12"]

    def test_month_nine_is_january_2003(self):
        result = months_since_200204_to_dates([9])
        assert result == ["2003-01"]

    def test_month_twelve_is_april_2003(self):
        result = months_since_200204_to_dates([12])
        assert result == ["2003-04"]

    def test_multiple_months(self):
        result = months_since_200204_to_dates([0, 6, 12])
        assert result == ["2002-04", "2002-10", "2003-04"]

    def test_output_format_yyyy_mm(self):
        result = months_since_200204_to_dates([0, 1, 2])
        import re
        for d in result:
            assert re.match(r"^\d{4}-\d{2}$", d), f"Date '{d}' not in YYYY-MM format"


class TestComputeRegionalTimeseries:
    """Verify regional timeseries computation."""

    def test_returns_expected_keys(self, grace_data):
        dates = months_since_200204_to_dates(grace_data["time_months_since_200204"])
        result = compute_regional_timeseries(
            grace_data["tws_anomaly_cm"],
            grace_data["lat"],
            grace_data["lon"],
            dates,
        )
        expected_keys = {
            "monthly_mean", "annual_mean", "annual_years",
            "trend_per_month", "trend_per_year", "r_squared", "p_value",
        }
        assert expected_keys <= set(result.keys())

    def test_trend_is_finite(self, grace_data):
        dates = months_since_200204_to_dates(grace_data["time_months_since_200204"])
        result = compute_regional_timeseries(
            grace_data["tws_anomaly_cm"],
            grace_data["lat"],
            grace_data["lon"],
            dates,
        )
        assert np.isfinite(result["trend_per_year"])
        assert np.isfinite(result["trend_per_month"])

    def test_monthly_mean_length(self, grace_data):
        dates = months_since_200204_to_dates(grace_data["time_months_since_200204"])
        result = compute_regional_timeseries(
            grace_data["tws_anomaly_cm"],
            grace_data["lat"],
            grace_data["lon"],
            dates,
        )
        assert len(result["monthly_mean"]) == len(dates)

    def test_annual_years_sorted(self, grace_data):
        dates = months_since_200204_to_dates(grace_data["time_months_since_200204"])
        result = compute_regional_timeseries(
            grace_data["tws_anomaly_cm"],
            grace_data["lat"],
            grace_data["lon"],
            dates,
        )
        years = result["annual_years"]
        assert years == sorted(years)

    def test_r_squared_in_range(self, grace_data):
        dates = months_since_200204_to_dates(grace_data["time_months_since_200204"])
        result = compute_regional_timeseries(
            grace_data["tws_anomaly_cm"],
            grace_data["lat"],
            grace_data["lon"],
            dates,
        )
        assert 0 <= result["r_squared"] <= 1


class TestComputeImpactMetrics:
    """Verify human impact metric computation."""

    def test_returns_expected_keys(self, grace_data, gpm_data, pop_data):
        result = compute_impact_metrics(grace_data, gpm_data, pop_data)
        expected = {
            "population_total", "population_declining_water",
            "population_severe_decline", "pct_affected", "pct_severe",
            "state_impacts", "tws_trend_grid", "precip_change_grid",
        }
        assert expected <= set(result.keys())

    def test_population_total_positive(self, grace_data, gpm_data, pop_data):
        result = compute_impact_metrics(grace_data, gpm_data, pop_data)
        assert result["population_total"] > 0

    def test_pct_affected_in_range(self, grace_data, gpm_data, pop_data):
        result = compute_impact_metrics(grace_data, gpm_data, pop_data)
        assert 0 <= result["pct_affected"] <= 100

    def test_pct_severe_in_range(self, grace_data, gpm_data, pop_data):
        result = compute_impact_metrics(grace_data, gpm_data, pop_data)
        assert 0 <= result["pct_severe"] <= 100

    def test_severe_subset_of_declining(self, grace_data, gpm_data, pop_data):
        result = compute_impact_metrics(grace_data, gpm_data, pop_data)
        assert result["population_severe_decline"] <= result["population_declining_water"]

    def test_stress_classifications_valid(self, grace_data, gpm_data, pop_data):
        result = compute_impact_metrics(grace_data, gpm_data, pop_data)
        valid_stress = {"severe", "moderate", "stable"}
        for state, info in result["state_impacts"].items():
            assert info["water_stress"] in valid_stress, (
                f"{state} has invalid stress: {info['water_stress']}"
            )

    def test_stress_thresholds_correct(self, grace_data, gpm_data, pop_data):
        """Verify that stress labels match the documented thresholds."""
        result = compute_impact_metrics(grace_data, gpm_data, pop_data)
        for state, info in result["state_impacts"].items():
            trend = info["tws_trend_cm_per_year"]
            stress = info["water_stress"]
            if trend < -1.5:
                assert stress == "severe", f"{state}: trend {trend} should be severe"
            elif trend < -0.5:
                assert stress == "moderate", f"{state}: trend {trend} should be moderate"
            else:
                assert stress == "stable", f"{state}: trend {trend} should be stable"

    def test_all_states_in_impacts(self, grace_data, gpm_data, pop_data):
        from pipeline.config import STATES
        result = compute_impact_metrics(grace_data, gpm_data, pop_data)
        for state in STATES:
            assert state in result["state_impacts"], f"Missing state: {state}"
