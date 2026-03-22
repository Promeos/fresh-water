"""
Fetch GRACE/GRACE-FO Mascon data for water storage anomalies.

Uses NASA JPL GRACE/GRACE-FO RL06.1 Mascon CRI gridded data.
This dataset provides monthly terrestrial water storage (TWS) anomalies
in centimeters of equivalent water thickness.

Data source: https://podaac.jpl.nasa.gov/
No authentication required for the pre-processed monthly summary files.
"""

import logging
from pathlib import Path

import numpy as np
import requests

from pipeline.config import NASA_API_KEY, RAW_DIR, REGION

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# NASA CMR API to search for the latest GRACE-FO granule
CMR_SEARCH_URL = "https://cmr.earthdata.nasa.gov/search/granules.json"
GRACE_COLLECTION = "C3195527175-POCLOUD"  # RL06.3 V4 (latest as of 2026)


def _find_latest_grace_granule() -> str | None:
    """Query NASA CMR for the latest GRACE-FO mascon NetCDF download URL."""
    params = {
        "collection_concept_id": GRACE_COLLECTION,
        "sort_key": "-start_date",
        "page_size": 1,
    }

    try:
        resp = requests.get(CMR_SEARCH_URL, params=params, timeout=30)
        resp.raise_for_status()
        entries = resp.json().get("feed", {}).get("entry", [])

        if not entries:
            logger.warning("No GRACE granules found via CMR search.")
            return None

        # Get download links
        links = entries[0].get("links", [])
        for link in links:
            href = link.get("href", "")
            if href.endswith(".nc") and "opendap" not in href.lower():
                logger.info(f"Found GRACE granule: {entries[0].get('title')}")
                return href

        # Fallback to first data link
        for link in links:
            href = link.get("href", "")
            if href.endswith(".nc"):
                return href

        logger.warning("No .nc download link found in CMR results.")
        return None

    except requests.RequestException as e:
        logger.warning(f"CMR search failed: {e}")
        return None


def _download_with_auth(url: str, output_path: Path) -> bool:
    """Download a file from NASA Earthdata using Bearer token auth."""
    if not NASA_API_KEY:
        logger.warning("No NASA_API_KEY found in .env — cannot authenticate.")
        return False

    headers = {"Authorization": f"Bearer {NASA_API_KEY}"}

    try:
        response = requests.get(
            url, headers=headers, stream=True, timeout=600, allow_redirects=True
        )
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0 and downloaded % (10 * 1024 * 1024) < 8192:
                    pct = (downloaded / total_size) * 100
                    logger.info(f"  Progress: {pct:.0f}%")

        logger.info(f"Downloaded {downloaded / 1024 / 1024:.1f} MB")
        return True

    except requests.RequestException as e:
        logger.error(f"Authenticated download failed: {e}")
        if output_path.exists():
            output_path.unlink()
        return False


def fetch_grace_data(output_dir: Path = RAW_DIR) -> Path:
    """
    Download GRACE/GRACE-FO mascon NetCDF file.

    The file is ~150 MB and contains monthly global terrestrial water
    storage (TWS) anomalies in cm of equivalent water thickness from
    April 2002 to the most recent available month.

    Attempts to download real data from NASA Earthdata using your API
    token (``NASA_API_KEY``).  Falls back to
    ``_generate_sample_grace_data`` so the pipeline can still run in
    development/demo mode.

    Args:
        output_dir: Directory to save the downloaded file.

    Returns:
        Path to the downloaded (or synthetically generated) NetCDF file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "grace_mascon.nc"

    if output_path.exists():
        logger.info(f"GRACE data already exists at {output_path}")
        return output_path

    # Try to find and download real data
    logger.info("Searching NASA CMR for latest GRACE-FO mascon data...")
    download_url = _find_latest_grace_granule()

    if download_url:
        logger.info("Downloading GRACE-FO data from NASA Earthdata...")
        if _download_with_auth(download_url, output_path):
            logger.info(f"GRACE data saved to {output_path}")
            return output_path

    logger.info("Falling back to sample data for development...")
    return _generate_sample_grace_data(output_path)


def _generate_sample_grace_data(output_path: Path) -> Path:
    """Generate synthetic GRACE TWS anomaly NetCDF for development/demo."""
    import netCDF4 as nc

    logger.info("Generating sample GRACE data for contiguous US...")

    # Monthly timestamps from 2002-04 to 2026-02
    n_months = (2026 - 2002) * 12 - 1  # Apr 2002 to Feb 2026

    # Grid covering contiguous US at 0.5 degree resolution
    lats = np.arange(REGION["min_lat"], REGION["max_lat"] + 0.5, 0.5)
    lons = np.arange(REGION["min_lon"], REGION["max_lon"] + 0.5, 0.5)

    # Generate realistic TWS anomalies (cm equivalent water thickness).
    # The synthetic signal is built from additive components designed
    # to mimic real GRACE observations across the US:
    #   1. Seasonal cycle  -- cosine wave peaking in Feb/Mar (snowpack + rain)
    #   2. Long-term trend -- varies regionally (SW declining, SE stable, etc.)
    #   3. Drought pulses  -- regional drought events
    #   4. Longitude-based pattern -- Eastern US generally wetter/stable
    #   5. Random noise    -- Gaussian noise for month-to-month variability
    # Fixed seed ensures reproducible output across runs.
    np.random.seed(42)
    n_lat, n_lon = len(lats), len(lons)
    tws = np.zeros((n_months, n_lat, n_lon))

    lat_grid, lon_grid = np.meshgrid(lats, lons, indexing="ij")

    # Regional trend patterns (cm/yr decline strength):
    # - Southwest (AZ, NM, S-CA): strongest decline
    # - Central Valley CA: severe decline
    # - High Plains (KS, NE, TX panhandle): Ogallala aquifer depletion
    # - Southeast: relatively stable/gaining
    # - Great Lakes/Northeast: stable to gaining
    sw_weight = np.clip((38.0 - lat_grid) / 8.0, 0, 1) * np.clip(
        (-108.0 - lon_grid) / 15.0, 0, 1
    )
    # High Plains: centered ~37N, -100W
    hp_dist = np.sqrt(((lat_grid - 37.0) / 5.0) ** 2 + ((lon_grid + 100.0) / 5.0) ** 2)
    hp_weight = np.exp(-hp_dist**2 / 2.0) * 0.6
    # Eastern US: generally stable to positive
    east_weight = np.clip((lon_grid + 90.0) / 25.0, 0, 1) * 0.3
    # Combined trend strength: negative in west/plains, positive in east
    trend_strength = np.clip(sw_weight + hp_weight - east_weight, -0.3, 1.0)

    for i in range(n_months):
        month_idx = i % 12
        year_frac = i / 12.0

        # 1. Seasonal cycle: amplitude varies by latitude
        seasonal_amp = 6.0 + 4.0 * np.clip((lat_grid - 30.0) / 20.0, 0, 1)
        seasonal = seasonal_amp * np.cos(2 * np.pi * (month_idx - 2) / 12.0)

        # 2. Long-term trend
        trend = -0.15 * year_frac * trend_strength

        # 3. Spatial variation (stationary pattern for grid texture)
        spatial = 3.0 * np.sin(np.radians(lat_grid) * 8) * np.cos(np.radians(lon_grid) * 6)

        # 4. Drought events (regional)
        drought_signal = np.zeros_like(lat_grid)
        # Western drought periods
        west_mask = lon_grid < -104
        if 108 <= i <= 132:  # ~2011-2013
            drought_signal += np.where(west_mask, -5.0 * trend_strength, 0)
        elif 144 <= i <= 180:  # 2014-2017 CA mega-drought
            ca_mask = (lat_grid > 32) & (lat_grid < 42) & (lon_grid < -114)
            drought_signal += np.where(ca_mask, -10.0, 0)
            drought_signal += np.where(west_mask & ~ca_mask, -4.0 * trend_strength, 0)
        elif 216 <= i <= 252:  # 2020-2022 Western mega-drought
            drought_signal += np.where(west_mask, -12.0 * trend_strength, 0)
        elif 253 <= i <= 270:  # 2023-2024 partial recovery
            drought_signal += np.where(west_mask, -4.0 * trend_strength, 0)
        elif i > 270:  # 2025-2026 renewed stress
            drought_signal += np.where(west_mask, -7.0 * trend_strength, 0)
        # Southeast flooding years (positive anomaly)
        se_mask = (lat_grid < 36) & (lon_grid > -90)
        if 180 <= i <= 192:  # ~2017 hurricane season
            drought_signal += np.where(se_mask, 8.0, 0)
        # High Plains Ogallala steady decline
        drought_signal += np.where(hp_dist < 2.5, -0.01 * year_frac, 0)

        # 5. Random noise
        noise = np.random.normal(0, 2.0, (n_lat, n_lon))

        tws[i] = seasonal + trend + spatial + drought_signal + noise

    # Write to NetCDF
    ds = nc.Dataset(output_path, "w", format="NETCDF4")

    ds.createDimension("time", n_months)
    ds.createDimension("lat", n_lat)
    ds.createDimension("lon", n_lon)

    time_var = ds.createVariable("time", "f8", ("time",))
    time_var.units = "months since 2002-04-01"
    time_var[:] = np.arange(n_months)

    lat_var = ds.createVariable("lat", "f8", ("lat",))
    lat_var.units = "degrees_north"
    lat_var[:] = lats

    lon_var = ds.createVariable("lon", "f8", ("lon",))
    lon_var.units = "degrees_east"
    lon_var[:] = lons

    lwe_var = ds.createVariable("lwe_thickness", "f4", ("time", "lat", "lon"), zlib=True)
    lwe_var.units = "cm"
    lwe_var.long_name = "Liquid Water Equivalent Thickness"
    lwe_var[:] = tws

    ds.title = "Sample GRACE-like TWS Anomaly Data (Contiguous US)"
    ds.source = "Synthetic data for development - patterns based on real GRACE observations"
    ds.close()

    logger.info(f"Sample GRACE data saved to {output_path}")
    return output_path


def load_grace_data(filepath: Path | None = None) -> dict:
    """
    Load and extract GRACE data for the Western US region.

    Handles both real NASA data (global, lon 0-360, time in days)
    and sample data (regional, lon -180 to 180, time in months).

    Returns:
        Dict with lat, lon, time_months_since_200204, and tws_anomaly_cm.
    """
    import netCDF4 as nc

    if filepath is None:
        filepath = RAW_DIR / "grace_mascon.nc"

    if not filepath.exists():
        filepath = fetch_grace_data()

    ds = nc.Dataset(filepath, "r")

    lats = ds.variables["lat"][:]
    lons_raw = ds.variables["lon"][:]
    time_raw = ds.variables["time"][:]
    time_units = ds.variables["time"].units
    tws = ds.variables["lwe_thickness"][:]

    # Apply scale factor if present (real GRACE data)
    if "scale_factor" in ds.variables:
        scale = ds.variables["scale_factor"][:]
        land_mask = ds.variables["land_mask"][:]
        # Apply CRI scale factor to land cells
        for t in range(tws.shape[0]):
            tws[t] = np.where(land_mask > 0.5, tws[t] * scale, tws[t])

    # Convert longitude from 0-360 to -180 to 180 if needed
    if lons_raw.max() > 180:
        lons = np.where(lons_raw > 180, lons_raw - 360, lons_raw)
        # Sort by new longitude values
        sort_idx = np.argsort(lons)
        lons = lons[sort_idx]
        tws = tws[:, :, sort_idx]
    else:
        lons = lons_raw

    # Convert time: real data uses "days since 2002-01-01",
    # we normalize to months since 2002-04 for consistency
    if "days" in time_units:
        # Convert days to approximate month index since 2002-04
        time_months = (time_raw - 90) / 30.4375  # ~90 days from Jan to Apr
        time_months = time_months.data
    else:
        time_months = time_raw.data

    # Subset to Western US
    lat_mask = (lats >= REGION["min_lat"]) & (lats <= REGION["max_lat"])
    lon_mask = (lons >= REGION["min_lon"]) & (lons <= REGION["max_lon"])

    tws_subset = tws[:, lat_mask, :][:, :, lon_mask]

    # Handle masked arrays (ocean/missing data → 0)
    if hasattr(tws_subset, 'filled'):
        tws_subset = tws_subset.filled(0.0)

    result = {
        "lat": lats[lat_mask].data.tolist(),
        "lon": lons[lon_mask].tolist() if hasattr(lons[lon_mask], 'tolist') else lons[lon_mask].data.tolist(),
        "time_months_since_200204": time_months.tolist(),
        "tws_anomaly_cm": tws_subset.tolist(),
    }

    ds.close()

    logger.info(
        f"Loaded GRACE data: {len(result['lat'])} lats x "
        f"{len(result['lon'])} lons x {len(result['time_months_since_200204'])} months"
    )
    return result


if __name__ == "__main__":
    filepath = fetch_grace_data()
    data = load_grace_data(filepath)
    logger.info(
        f"Loaded GRACE data: {len(data['lat'])} lats x "
        f"{len(data['lon'])} lons x "
        f"{len(data['time_months_since_200204'])} months"
    )
