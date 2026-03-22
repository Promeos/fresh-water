"""
Process satellite and population data to compute water security metrics.

Combines GRACE water storage, GPM precipitation, and population data
to produce human-impact analysis of freshwater changes across the United States.
"""

import logging
from datetime import datetime

import numpy as np
from scipy import stats

from pipeline.config import REGION
from pipeline.fetch_gpm import fetch_gpm_data, load_gpm_data
from pipeline.fetch_grace import fetch_grace_data, load_grace_data
from pipeline.fetch_population import generate_population_data, load_population_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _align_to_grace_grid(gpm_data: dict, grace_data: dict) -> dict:
    """
    Resample GPM data to match GRACE spatial and temporal dimensions.

    GRACE and GPM may have different grid sizes and time lengths.
    GPM is spatially interpolated (bilinear via ``scipy.ndimage.zoom``)
    and temporally truncated to the shorter of the two records.

    Args:
        gpm_data: Output of :func:`pipeline.fetch_gpm.load_gpm_data`.
        grace_data: Output of :func:`pipeline.fetch_grace.load_grace_data`.

    Returns:
        Dict with the same keys as *gpm_data* (``lat``, ``lon``,
        ``time_months_since_200204``, ``precipitation_mm``) but with
        spatial and temporal dimensions matching *grace_data*.
    """
    from scipy.ndimage import zoom

    gpm_arr = np.array(gpm_data["precipitation_mm"])
    grace_arr = np.array(grace_data["tws_anomaly_cm"])
    g_time, g_lat, g_lon = grace_arr.shape
    p_time, p_lat, p_lon = gpm_arr.shape

    # Temporal alignment: truncate to the shorter length
    n_time = min(g_time, p_time)
    gpm_arr = gpm_arr[:n_time]

    # Spatial alignment: zoom GPM to match GRACE grid
    if (p_lat, p_lon) != (g_lat, g_lon):
        zoom_factors = (1, g_lat / p_lat, g_lon / p_lon)
        gpm_arr = zoom(gpm_arr, zoom_factors, order=1)

    return {
        "lat": grace_data["lat"],
        "lon": grace_data["lon"],
        "time_months_since_200204": grace_data["time_months_since_200204"][:n_time],
        "precipitation_mm": gpm_arr.tolist(),
    }


def months_since_200204_to_dates(months_array: list) -> list[str]:
    """Convert month offsets (from April 2002) to ``YYYY-MM`` date strings."""
    dates = []
    for m in months_array:
        m_int = round(m)
        year = 2002 + (3 + m_int) // 12
        month = (3 + m_int) % 12 + 1
        dates.append(f"{year:04d}-{month:02d}")
    return dates


def compute_regional_timeseries(data_3d: list, lats: list, lons: list, dates: list[str]) -> dict:
    """
    Compute area-weighted regional average timeseries with trend.

    Groups annual averages by calendar year (includes partial years
    with 3+ months of data).

    Args:
        data_3d: Nested list with shape [time x lat x lon].
        lats: Latitude values (degrees north), used for cosine
            area-weighting.
        lons: Longitude values (degrees east).
        dates: ``YYYY-MM`` date strings, one per timestep.

    Returns:
        Dict with keys:
            - ``"monthly_mean"`` (list[float]): Area-weighted regional
              mean for each month.
            - ``"annual_mean"`` (list[float]): Calendar-year averages
              (only years with >= 3 months).
            - ``"annual_years"`` (list[int]): Years corresponding to
              *annual_mean*.
            - ``"trend_per_month"`` (float): OLS slope per month
              (input units / month).
            - ``"trend_per_year"`` (float): OLS slope annualized
              (input units / year).
            - ``"r_squared"`` (float): Coefficient of determination.
            - ``"p_value"`` (float): Two-sided p-value for the slope.
    """
    arr = np.array(data_3d)
    n_time = arr.shape[0]

    # Area-weighted average (cosine of latitude)
    lat_arr = np.array(lats)
    weights = np.cos(np.radians(lat_arr))
    weights_2d = weights[:, np.newaxis] * np.ones(len(lons))
    weights_3d = np.broadcast_to(weights_2d, arr.shape)

    monthly_mean = np.average(
        arr.reshape(n_time, -1), weights=weights_3d.reshape(n_time, -1), axis=1
    )

    # Annual averages grouped by calendar year
    year_to_values = {}
    for i, date_str in enumerate(dates[:n_time]):
        year = int(date_str.split("-")[0])
        year_to_values.setdefault(year, []).append(monthly_mean[i])

    annual_years = []
    annual_mean = []
    for year in sorted(year_to_values.keys()):
        values = year_to_values[year]
        if len(values) >= 3:  # Need at least 3 months for a meaningful average
            annual_years.append(year)
            annual_mean.append(float(np.mean(values)))

    # Linear trend
    x = np.arange(n_time)
    slope, _intercept, r_value, p_value, _std_err = stats.linregress(x, monthly_mean)

    return {
        "monthly_mean": monthly_mean.tolist(),
        "annual_mean": annual_mean,
        "annual_years": annual_years,
        "trend_per_month": float(slope),
        "trend_per_year": float(slope * 12),
        "r_squared": float(r_value**2),
        "p_value": float(p_value),
    }


def compute_spatial_trends(data_3d: list, lats: list, lons: list) -> dict:
    """
    Compute per-pixel linear trends over time.

    Fits an independent OLS regression at every grid cell.  Pixels
    containing any non-finite value are set to NaN.

    Args:
        data_3d: Nested list with shape [time x lat x lon].
        lats: Latitude values (degrees north).
        lons: Longitude values (degrees east).

    Returns:
        Dict with keys:
            - ``"lat"`` (list[float]): Latitude values.
            - ``"lon"`` (list[float]): Longitude values.
            - ``"trend_per_year"`` (list): Grid of linear trend slopes
              (input-unit/year), shape [lat x lon].
    """
    arr = np.array(data_3d)
    n_time, n_lat, n_lon = arr.shape

    trend_grid = np.zeros((n_lat, n_lon))
    x = np.arange(n_time)

    for i in range(n_lat):
        for j in range(n_lon):
            y = arr[:, i, j]
            if np.all(np.isfinite(y)):
                slope, _, _, _, _ = stats.linregress(x, y)
                trend_grid[i, j] = slope * 12  # per year
            else:
                trend_grid[i, j] = np.nan

    return {
        "lat": lats,
        "lon": lons,
        "trend_per_year": trend_grid.tolist(),
    }


def compute_impact_metrics(grace_data: dict, gpm_data: dict, pop_data: dict) -> dict:
    """
    Compute human impact metrics by combining water and population data.

    Overlays per-pixel TWS trends (cm/year) with 2023 population to
    estimate how many people live in areas of declining water storage.
    Also computes a precipitation deficit (%) comparing the most recent
    36 months to the historical average.

    Water-stress thresholds (applied per pixel):
        - *stable*: TWS trend >= -0.5 cm/year
        - *moderate*: TWS trend < -0.5 cm/year
        - *severe*: TWS trend < -1.5 cm/year

    Args:
        grace_data: Output of :func:`pipeline.fetch_grace.load_grace_data`.
        gpm_data: Output of :func:`pipeline.fetch_gpm.load_gpm_data`.
        pop_data: Output of
            :func:`pipeline.fetch_population.load_population_data`.

    Returns:
        Dict with keys:
            - ``"population_total"`` (int): Total regional population.
            - ``"population_declining_water"`` (int): Population in
              pixels with TWS trend < -0.5 cm/year.
            - ``"population_severe_decline"`` (int): Population in
              pixels with TWS trend < -1.5 cm/year.
            - ``"pct_affected"`` (float): Percent of population in
              declining areas.
            - ``"pct_severe"`` (float): Percent in severe-decline areas.
            - ``"state_impacts"`` (dict): Per-state metrics including
              trend (cm/year), precipitation change (%), stress label,
              and monthly timeseries for dashboard sparklines.
            - ``"tws_trend_grid"`` (dict): Lat/lon + [lat x lon] trend
              values (cm/year).
            - ``"precip_change_grid"`` (dict): Lat/lon + [lat x lon]
              precipitation change values (%).
    """
    tws = np.array(grace_data["tws_anomaly_cm"])
    precip = np.array(gpm_data["precipitation_mm"])
    # Align time dimensions
    n_time = min(tws.shape[0], precip.shape[0])
    tws = tws[:n_time]
    precip = precip[:n_time]

    # Latest available population grid (2023)
    # Interpolate population to match GRACE grid if sizes differ
    pop_raw = np.array(pop_data["gridded_population"]["2023"])
    n_lat, n_lon = tws.shape[1], tws.shape[2]

    if pop_raw.shape != (n_lat, n_lon):
        from scipy.ndimage import zoom

        zoom_factors = (n_lat / pop_raw.shape[0], n_lon / pop_raw.shape[1])
        pop_grid = zoom(pop_raw, zoom_factors, order=1)
        # Rescale to preserve total population
        pop_grid *= pop_raw.sum() / pop_grid.sum()
    else:
        pop_grid = pop_raw

    # Compute TWS trend per pixel (cm/year)
    x = np.arange(n_time)
    tws_trend = np.zeros((n_lat, n_lon))

    for i in range(n_lat):
        for j in range(n_lon):
            slope, _, _, _, _ = stats.linregress(x, tws[:, i, j])
            tws_trend[i, j] = slope * 12

    # Water stress classification thresholds (cm/year TWS trend).
    # These thresholds are based on published GRACE drought analyses:
    #   - Stable:   >= -0.5 cm/yr  (normal interannual variability)
    #   - Moderate:  < -0.5 cm/yr  (sustained net loss, warrants monitoring)
    #   - Severe:    < -1.5 cm/yr  (significant depletion, e.g., CA Central Valley)
    declining_mask = tws_trend < -0.5
    severe_mask = tws_trend < -1.5

    pop_declining = float(np.sum(pop_grid[declining_mask]))
    pop_severe = float(np.sum(pop_grid[severe_mask]))
    pop_total = float(np.sum(pop_grid))

    # Precipitation deficit: compare the most recent 3 years (36 months) to
    # the full historical record before them. This highlights whether current
    # conditions are wetter or drier than the long-term norm, helping
    # distinguish temporary dry spells from persistent drought.
    n_recent = min(36, n_time)
    n_historical = n_time - n_recent
    if n_historical > 0:
        hist_avg = precip[:n_historical].mean(axis=0)
        recent_avg = precip[-n_recent:].mean(axis=0)
        precip_change_pct = np.where(
            hist_avg > 0,
            ((recent_avg - hist_avg) / hist_avg) * 100,
            0,
        )
    else:
        precip_change_pct = np.zeros((n_lat, n_lon))

    # State-level summary
    state_impacts = {}
    for state, info in pop_data["state_summary"].items():
        clat, clon = info["center_lat"], info["center_lon"]

        # Find nearest grid cell
        lat_idx = np.argmin(np.abs(np.array(grace_data["lat"]) - clat))
        lon_idx = np.argmin(np.abs(np.array(grace_data["lon"]) - clon))

        # Get trend and recent change at state center
        state_tws_trend = float(tws_trend[lat_idx, lon_idx])

        # Get full timeseries at state center for sparkline
        state_tws_ts = tws[:, lat_idx, lon_idx].tolist()
        state_precip_ts = precip[:, lat_idx, lon_idx].tolist()

        state_impacts[state] = {
            "population": info["population_2023"],
            "tws_trend_cm_per_year": round(state_tws_trend, 2),
            "precip_change_pct": round(float(precip_change_pct[lat_idx, lon_idx]), 1),
            "water_stress": (
                "severe"
                if state_tws_trend < -1.5
                else "moderate"
                if state_tws_trend < -0.5
                else "stable"
            ),
            "tws_timeseries": [round(v, 2) for v in state_tws_ts],
            "precip_timeseries": [round(v, 1) for v in state_precip_ts],
        }

    return {
        "population_total": int(pop_total),
        "population_declining_water": int(pop_declining),
        "population_severe_decline": int(pop_severe),
        "pct_affected": round(pop_declining / pop_total * 100, 1),
        "pct_severe": round(pop_severe / pop_total * 100, 1),
        "state_impacts": state_impacts,
        "tws_trend_grid": {
            "lat": grace_data["lat"],
            "lon": grace_data["lon"],
            "values": tws_trend.tolist(),
        },
        "precip_change_grid": {
            "lat": grace_data["lat"],
            "lon": grace_data["lon"],
            "values": precip_change_pct.tolist(),
        },
    }


def run_pipeline() -> dict:
    """
    Run the full data processing pipeline.

    Orchestrates four stages:
        1. Fetch (or generate) GRACE, GPM, and population data.
        2. Compute area-weighted regional timeseries.
        3. Compute per-pixel spatial trends.
        4. Overlay population for human-impact analysis.

    Returns:
        Nested dict ready for :func:`pipeline.export.export_for_frontend`
        with top-level keys ``"metadata"``, ``"timeseries"``,
        ``"spatial"``, and ``"impact"``.
    """
    logger.info("=" * 60)
    logger.info("Fresh Water Monitoring Pipeline - United States")
    logger.info("=" * 60)

    # Step 1: Fetch/generate data
    logger.info("\n[1/4] Fetching GRACE-FO water storage data...")
    fetch_grace_data()
    grace = load_grace_data()

    logger.info("\n[2/4] Fetching GPM precipitation data...")
    fetch_gpm_data()
    gpm = load_gpm_data()

    logger.info("\n[3/4] Loading population data...")
    generate_population_data()
    pop = load_population_data()

    # Step 2: Align GPM grid to GRACE grid (they may differ)
    logger.info("\n[4/4] Computing analysis...")
    gpm = _align_to_grace_grid(gpm, grace)

    dates = months_since_200204_to_dates(grace["time_months_since_200204"])

    tws_timeseries = compute_regional_timeseries(
        grace["tws_anomaly_cm"], grace["lat"], grace["lon"], dates
    )
    precip_timeseries = compute_regional_timeseries(
        gpm["precipitation_mm"], gpm["lat"], gpm["lon"], dates
    )

    # Step 3: Compute spatial trends
    tws_spatial = compute_spatial_trends(grace["tws_anomaly_cm"], grace["lat"], grace["lon"])

    # Step 4: Human impact analysis
    impact = compute_impact_metrics(grace, gpm, pop)

    results = {
        "metadata": {
            "region": REGION["name"],
            "date_range": f"{dates[0]} to {dates[-1]}",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "data_sources": [
                "GRACE/GRACE-FO JPL Mascon RL06.3 V04 (water storage)",
                "GPM IMERG V07 (precipitation)",
                "US Census Bureau (population)",
            ],
        },
        "timeseries": {
            "dates": dates,
            "years": tws_timeseries["annual_years"],
            "tws_anomaly_cm": tws_timeseries["monthly_mean"],
            "tws_annual_cm": tws_timeseries["annual_mean"],
            "tws_trend_cm_per_year": tws_timeseries["trend_per_year"],
            "precipitation_mm": precip_timeseries["monthly_mean"],
            "precip_annual_mm": precip_timeseries["annual_mean"],
            "precip_trend_mm_per_year": precip_timeseries["trend_per_year"],
        },
        "spatial": {
            "lat": tws_spatial["lat"],
            "lon": tws_spatial["lon"],
            "tws_trend": tws_spatial["trend_per_year"],
        },
        "impact": impact,
    }

    logger.info("\n" + "=" * 60)
    logger.info("Pipeline complete!")
    logger.info(f"  Region: {REGION['name']}")
    logger.info(f"  Period: {dates[0]} to {dates[-1]}")
    logger.info(f"  TWS trend: {tws_timeseries['trend_per_year']:.2f} cm/year")
    logger.info(
        f"  Population affected by decline: "
        f"{impact['population_declining_water']:,} "
        f"({impact['pct_affected']}%)"
    )
    logger.info("=" * 60)

    return results


if __name__ == "__main__":
    results = run_pipeline()
