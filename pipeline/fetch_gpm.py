"""
Fetch GPM IMERG precipitation data.

Uses NASA Global Precipitation Measurement (GPM) IMERG V07 monthly data
to track precipitation patterns across the United States.

Data source: https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGM_07/summary
Individual monthly files are downloaded from GES DISC, subset to the
US region, and combined into a single NetCDF file.
"""

import logging
from pathlib import Path

import numpy as np
import requests

from pipeline.config import NASA_API_KEY, RAW_DIR, REGION

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CMR collection for GPM IMERG V07 monthly (Final Run)
GPM_COLLECTION = "C2723754851-GES_DISC"
CMR_SEARCH_URL = "https://cmr.earthdata.nasa.gov/search/granules.json"

# Start/end for download (GRACE starts Apr 2002; GPM IMERG V07 starts Jun 2000)
GPM_START_YEAR, GPM_START_MONTH = 2002, 4
GPM_END_YEAR, GPM_END_MONTH = 2026, 2


def _find_gpm_granule_urls() -> list[tuple[int, int, str]]:
    """Search NASA CMR for all GPM IMERG monthly granule download URLs.

    Returns list of (year, month, url) tuples sorted by date.
    """
    results = []
    page = 1
    page_size = 200

    start = f"{GPM_START_YEAR:04d}-{GPM_START_MONTH:02d}-01T00:00:00Z"
    end = f"{GPM_END_YEAR:04d}-{GPM_END_MONTH:02d}-28T23:59:59Z"

    while True:
        try:
            resp = requests.get(
                CMR_SEARCH_URL,
                params={
                    "collection_concept_id": GPM_COLLECTION,
                    "temporal": f"{start},{end}",
                    "sort_key": "start_date",
                    "page_size": page_size,
                    "page_num": page,
                },
                timeout=30,
            )
            resp.raise_for_status()
            entries = resp.json().get("feed", {}).get("entry", [])

            if not entries:
                break

            for entry in entries:
                # Extract year/month from title like "...20240101-S000000..."
                for link in entry.get("links", []):
                    href = link.get("href", "")
                    if "data.gesdisc" in href and href.endswith(".HDF5"):
                        # Parse date from filename
                        parts = href.split("3IMERG.")
                        if len(parts) > 1:
                            date_str = parts[1][:8]
                            year = int(date_str[:4])
                            month = int(date_str[4:6])
                            results.append((year, month, href))
                        break

            if len(entries) < page_size:
                break
            page += 1

        except requests.RequestException as e:
            logger.warning(f"CMR search page {page} failed: {e}")
            break

    logger.info(f"  Found {len(results)} GPM granules via CMR")
    return sorted(results)


def _download_gpm_granule(url: str, output_path: Path) -> bool:
    """Download a single GPM file using NASA Earthdata Bearer token."""
    if not NASA_API_KEY:
        return False

    headers = {"Authorization": f"Bearer {NASA_API_KEY}"}
    try:
        resp = requests.get(
            url,
            headers=headers,
            timeout=180,
            allow_redirects=True,
            stream=True,
        )
        resp.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                f.write(chunk)
        return output_path.stat().st_size > 1000
    except requests.RequestException as e:
        logger.debug(f"GPM download failed: {e}")
        if output_path.exists():
            output_path.unlink()
        return False


def _extract_precip_from_granule(filepath: Path) -> np.ndarray | None:
    """Extract US-region precipitation (mm/month) from a GPM HDF5 granule."""
    import h5py

    try:
        with h5py.File(filepath, "r") as f:
            # GPM IMERG V07 structure: /Grid/precipitation [lon, lat]
            grid = f["Grid"]
            precip = grid["precipitation"][0]  # [lon, lat] — single time step
            lat = grid["lat"][:]
            lon = grid["lon"][:]

            # Transpose from [lon, lat] to [lat, lon]
            precip = precip.T

            # Subset to US region
            lat_mask = (lat >= REGION["min_lat"]) & (lat <= REGION["max_lat"])
            lon_mask = (lon >= REGION["min_lon"]) & (lon <= REGION["max_lon"])

            subset = precip[np.ix_(lat_mask, lon_mask)]

            # Convert from mm/hr to mm/month (approximate: 30.4 days * 24 hrs)
            subset = subset * 24.0 * 30.4375

            # Replace fill values with 0
            subset = np.where(subset < 0, 0, subset)

            return subset

    except Exception as e:
        logger.debug(f"Could not read GPM file {filepath}: {e}")
        return None


def fetch_gpm_data(output_dir: Path = RAW_DIR) -> Path:
    """
    Download GPM IMERG V07 monthly precipitation data.

    Downloads individual monthly granules from NASA GES DISC, extracts
    the US region, and combines into a single NetCDF file.  Falls back
    to synthetic data if authentication fails or files are unavailable.

    Args:
        output_dir: Directory to save the precipitation NetCDF file.

    Returns:
        Path to the precipitation NetCDF file (real or synthetic).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "gpm_precipitation.nc"

    if output_path.exists():
        logger.info(f"GPM data already exists at {output_path}")
        return output_path

    if not NASA_API_KEY:
        logger.info("No NASA_API_KEY — falling back to synthetic GPM data.")
        return _generate_sample_gpm_data(output_path)

    logger.info("Downloading GPM IMERG V07 monthly data from NASA GES DISC...")
    logger.info("  Searching CMR for available granules...")

    granule_list = _find_gpm_granule_urls()

    if not granule_list:
        logger.warning("No GPM granules found via CMR. Using synthetic data.")
        return _generate_sample_gpm_data(output_path)

    # Download each monthly granule
    tmp_dir = output_dir / "gpm_tmp"
    tmp_dir.mkdir(exist_ok=True)
    downloaded = []
    failed = 0

    for i, (year, month, url) in enumerate(granule_list):
        if (i + 1) % 24 == 0 or i == 0:
            logger.info(f"  Downloading {year}-{month:02d} ({i + 1}/{len(granule_list)})...")

        tmp_file = tmp_dir / f"gpm_{year:04d}{month:02d}.hdf5"

        if _download_gpm_granule(url, tmp_file):
            precip = _extract_precip_from_granule(tmp_file)
            if precip is not None:
                downloaded.append((year, month, precip))
            else:
                failed += 1
            # Clean up individual file to save disk
            tmp_file.unlink(missing_ok=True)
        else:
            failed += 1

        # If we fail too many times early, fall back to synthetic
        if failed > 10 and len(downloaded) < 3:
            logger.warning(
                f"Too many download failures ({failed}). Falling back to synthetic GPM data."
            )
            # Clean up tmp dir
            for f in tmp_dir.iterdir():
                f.unlink()
            tmp_dir.rmdir()
            return _generate_sample_gpm_data(output_path)

    # Clean up tmp dir
    for f in tmp_dir.iterdir():
        f.unlink()
    tmp_dir.rmdir()

    if not downloaded:
        logger.warning("No GPM granules downloaded. Using synthetic data.")
        return _generate_sample_gpm_data(output_path)

    logger.info(f"  Downloaded {len(downloaded)}/{len(granule_list)} months ({failed} failed)")

    # Combine into single NetCDF
    return _combine_gpm_to_netcdf(downloaded, output_path)


def _combine_gpm_to_netcdf(
    downloaded: list[tuple[int, int, np.ndarray]], output_path: Path
) -> Path:
    """Combine downloaded monthly GPM arrays (mm/month) into a single NetCDF file."""
    import netCDF4 as nc

    # Sort by date
    downloaded.sort(key=lambda x: (x[0], x[1]))
    n_months = len(downloaded)

    # Interpolate to 0.5-degree grid
    target_lats = np.arange(REGION["min_lat"], REGION["max_lat"] + 0.5, 0.5)
    target_lons = np.arange(REGION["min_lon"], REGION["max_lon"] + 0.5, 0.5)

    precip = np.zeros((n_months, len(target_lats), len(target_lons)))

    for i, (_year, _month, arr) in enumerate(downloaded):
        # Resample to target grid if needed
        if arr.shape != (len(target_lats), len(target_lons)):
            from scipy.ndimage import zoom

            zoom_y = len(target_lats) / arr.shape[0]
            zoom_x = len(target_lons) / arr.shape[1]
            precip[i] = zoom(arr, (zoom_y, zoom_x), order=1)
        else:
            precip[i] = arr

    # Compute time as months since 2002-04
    time_vals = []
    for year, month, _ in downloaded:
        months_offset = (year - 2002) * 12 + (month - 4)
        time_vals.append(months_offset)

    # Write NetCDF
    ds = nc.Dataset(output_path, "w", format="NETCDF4")
    ds.createDimension("time", n_months)
    ds.createDimension("lat", len(target_lats))
    ds.createDimension("lon", len(target_lons))

    time_var = ds.createVariable("time", "f8", ("time",))
    time_var.units = "months since 2002-04-01"
    time_var[:] = time_vals

    lat_var = ds.createVariable("lat", "f8", ("lat",))
    lat_var.units = "degrees_north"
    lat_var[:] = target_lats

    lon_var = ds.createVariable("lon", "f8", ("lon",))
    lon_var.units = "degrees_east"
    lon_var[:] = target_lons

    p_var = ds.createVariable("precipitation", "f4", ("time", "lat", "lon"), zlib=True)
    p_var.units = "mm/month"
    p_var.long_name = "Monthly Accumulated Precipitation"
    precip = np.maximum(0, precip)  # Ensure non-negative
    p_var[:] = precip

    ds.title = "GPM IMERG V07 Monthly Precipitation (US Region)"
    ds.source = "NASA GPM IMERG Final Run V07 monthly data from GES DISC"
    ds.close()

    logger.info(f"GPM data saved to {output_path} ({n_months} months)")
    return output_path


def _generate_sample_gpm_data(output_path: Path) -> Path:
    """Generate synthetic GPM precipitation NetCDF (mm/month) for development/demo."""
    import netCDF4 as nc

    logger.info("Generating sample GPM precipitation data for contiguous US...")

    n_months = (2026 - 2002) * 12 - 1  # Match GRACE timespan (Apr 2002 to Feb 2026)

    # Grid at 0.5 degree resolution
    lats = np.arange(REGION["min_lat"], REGION["max_lat"] + 0.5, 0.5)
    lons = np.arange(REGION["min_lon"], REGION["max_lon"] + 0.5, 0.5)
    n_lat, n_lon = len(lats), len(lons)

    np.random.seed(123)
    precip = np.zeros((n_months, n_lat, n_lon))

    lat_grid, lon_grid = np.meshgrid(lats, lons, indexing="ij")

    # Base precipitation pattern (mm/month) — US-wide
    # Southeast is wettest (~120mm/mo), desert SW driest (~15mm/mo),
    # Pacific NW wet coast, Great Plains moderate, Northeast moderate-wet
    base_precip = (
        50.0
        # East-west gradient: eastern US gets more rain
        + 40.0 * np.clip((lon_grid + 90.0) / 30.0, 0, 1)
        # Southeast enhancement (Gulf moisture)
        + 30.0 * np.clip((35.0 - lat_grid) / 10.0, 0, 1) * np.clip((lon_grid + 90.0) / 15.0, 0, 1)
        # Pacific coast enhancement
        + 25.0
        * np.exp(-(((lon_grid + 122.0) / 3.0) ** 2))
        * np.clip((lat_grid - 40.0) / 8.0, 0, 1)
        # Desert SW suppression (AZ, NM, NV, S-CA)
        - 35.0 * np.clip((36.0 - lat_grid) / 8.0, 0, 1) * np.clip((-108.0 - lon_grid) / 15.0, 0, 1)
    )
    base_precip = np.maximum(base_precip, 8.0)  # Floor at 8 mm/mo

    for i in range(n_months):
        month_idx = i % 12
        year_idx = i // 12

        # Seasonal cycle varies by region
        # West: wet winter / dry summer
        # East: more uniform, slight summer peak (thunderstorms)
        west_seasonal = np.where(
            np.isin(month_idx, [10, 11, 0, 1, 2]),
            1.8,
            np.where(np.isin(month_idx, [5, 6, 7, 8]), 0.3, 1.0),
        )
        east_seasonal = np.where(
            np.isin(month_idx, [5, 6, 7]), 1.3, np.where(np.isin(month_idx, [0, 1, 11]), 0.8, 1.0)
        )
        # Blend based on longitude
        east_frac = np.clip((lon_grid + 100.0) / 30.0, 0, 1)
        seasonal_factor = west_seasonal * (1 - east_frac) + east_seasonal * east_frac

        # ENSO cycle
        enso_cycle = 0.2 * np.sin(2 * np.pi * year_idx / 4.0)

        # Regional drought factors
        drought_factor = np.ones_like(lat_grid)
        west_mask = lon_grid < -104
        if 12 * 9 <= i <= 12 * 11:  # ~2011-2013
            drought_factor = np.where(west_mask, 0.7, drought_factor)
        elif 12 * 12 <= i <= 12 * 15:  # 2014-2017
            drought_factor = np.where(west_mask, 0.6, drought_factor)
        elif 12 * 18 <= i <= 12 * 21:  # 2020-2022
            drought_factor = np.where(west_mask, 0.55, drought_factor)

        # Combine
        monthly_precip = base_precip * seasonal_factor * drought_factor * (1.0 + enso_cycle)

        # Gamma noise (always non-negative, right-skewed)
        noise = np.random.gamma(shape=2, scale=5, size=(n_lat, n_lon))
        precip[i] = np.maximum(0, monthly_precip + noise - 10)

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

    precip_var = ds.createVariable("precipitation", "f4", ("time", "lat", "lon"), zlib=True)
    precip_var.units = "mm/month"
    precip_var.long_name = "Monthly Accumulated Precipitation"
    precip_var[:] = precip

    ds.title = "Sample GPM IMERG-like Precipitation Data (Contiguous US)"
    ds.source = "Synthetic data for development - patterns based on real GPM observations"
    ds.close()

    logger.info(f"Sample GPM data saved to {output_path}")
    return output_path


def load_gpm_data(filepath: Path | None = None) -> dict:
    """
    Load GPM precipitation data for the contiguous US.

    Reads the NetCDF file produced by :func:`fetch_gpm_data` and
    returns plain Python lists suitable for JSON serialization.

    Args:
        filepath: Path to a GPM precipitation NetCDF file.  When
            *None*, looks in ``RAW_DIR`` and fetches automatically
            if missing.

    Returns:
        Dict with keys:
            - ``"lat"`` (list[float]): Latitude values (degrees north).
            - ``"lon"`` (list[float]): Longitude values (degrees east).
            - ``"time_months_since_200204"`` (list[float]): Month offsets
              from April 2002.
            - ``"precipitation_mm"`` (list): Monthly accumulated
              precipitation in mm/month, shape [time x lat x lon].
    """
    import netCDF4 as nc

    if filepath is None:
        filepath = RAW_DIR / "gpm_precipitation.nc"

    if not filepath.exists():
        filepath = fetch_gpm_data()

    ds = nc.Dataset(filepath, "r")

    result = {
        "lat": ds.variables["lat"][:].data.tolist(),
        "lon": ds.variables["lon"][:].data.tolist(),
        "time_months_since_200204": ds.variables["time"][:].data.tolist(),
        "precipitation_mm": ds.variables["precipitation"][:].data.tolist(),
    }

    ds.close()
    return result


if __name__ == "__main__":
    filepath = fetch_gpm_data()
    data = load_gpm_data(filepath)
    logger.info(
        f"Loaded GPM data: {len(data['lat'])} lats x "
        f"{len(data['lon'])} lons x "
        f"{len(data['time_months_since_200204'])} months"
    )
