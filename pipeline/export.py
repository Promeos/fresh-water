"""
Export processed data as JSON files for the frontend dashboard.

Splits the analysis results into separate, compact JSON files so the
GitHub Pages frontend can lazy-load only the data each component needs.
All numeric values are rounded before export to keep file sizes small.

Output files (written to ``DATA_DIR``):
    - ``summary.json``    -- headline metrics and metadata; loaded on
      page init by the hero / KPI cards.
    - ``timeseries.json`` -- monthly and annual regional averages;
      consumed by the line-chart components.
    - ``spatial.json``    -- gridded TWS trend (cm/year) and
      precipitation change (%); consumed by the heatmap/map component.
    - ``states.json``     -- per-state impact details and sparkline
      timeseries; consumed by the state detail table/cards.
    - ``counties.json``   -- GeoJSON FeatureCollection with per-county
      TWS trend, water stress classification, and simplified polygon
      boundaries for map rendering.
"""

import json
import logging
from pathlib import Path

import numpy as np

from pipeline.config import DATA_DIR
from pipeline.fetch_counties import load_county_data
from pipeline.process import run_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def export_for_frontend(results: dict | None = None, output_dir: Path = DATA_DIR):
    """
    Export analysis results as JSON files for the GitHub Pages dashboard.

    Writes four JSON files (see module docstring for details on each).
    Values are rounded to reduce file size while preserving visual
    fidelity in the dashboard charts and maps.

    Args:
        results: Pipeline output dict from :func:`pipeline.process.run_pipeline`.
            When *None*, the pipeline is executed automatically.
        output_dir: Target directory for the JSON files.
    """
    if results is None:
        results = run_pipeline()

    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Summary: key metrics loaded on page init
    summary = {
        "metadata": results["metadata"],
        "headline": {
            "total_population": results["impact"]["population_total"],
            "population_affected": results["impact"]["population_declining_water"],
            "population_severe": results["impact"]["population_severe_decline"],
            "pct_affected": results["impact"]["pct_affected"],
            "pct_severe": results["impact"]["pct_severe"],
            "tws_trend_cm_per_year": results["timeseries"]["tws_trend_cm_per_year"],
            "precip_trend_mm_per_year": results["timeseries"]["precip_trend_mm_per_year"],
        },
    }
    _write_json(summary, output_dir / "summary.json")

    # 2. Timeseries: for line charts
    timeseries = {
        "dates": results["timeseries"]["dates"],
        "years": results["timeseries"]["years"],
        "tws_monthly": [round(v, 2) for v in results["timeseries"]["tws_anomaly_cm"]],
        "tws_annual": [round(v, 2) for v in results["timeseries"]["tws_annual_cm"]],
        "precip_monthly": [round(v, 1) for v in results["timeseries"]["precipitation_mm"]],
        "precip_annual": [round(v, 1) for v in results["timeseries"]["precip_annual_mm"]],
    }
    _write_json(timeseries, output_dir / "timeseries.json")

    # 3. Spatial: for heatmaps (larger file)
    spatial = {
        "lat": results["spatial"]["lat"],
        "lon": results["spatial"]["lon"],
        "tws_trend": [[round(v, 3) for v in row] for row in results["spatial"]["tws_trend"]],
        "precip_change": [
            [round(v, 1) for v in row] for row in results["impact"]["precip_change_grid"]["values"]
        ],
    }
    _write_json(spatial, output_dir / "spatial.json")

    # 4. State impacts: for the state detail table/cards
    states = {}
    for state, data in results["impact"]["state_impacts"].items():
        states[state] = {
            "population": data["population"],
            "tws_trend": data["tws_trend_cm_per_year"],
            "precip_change_pct": data["precip_change_pct"],
            "water_stress": data["water_stress"],
            "tws_timeseries": data["tws_timeseries"],
            "precip_timeseries": data["precip_timeseries"],
        }
    _write_json(
        {"dates": results["timeseries"]["dates"], "states": states},
        output_dir / "states.json",
    )

    # 5. Counties: GeoJSON with per-county TWS trend and water stress
    _export_counties(results, output_dir)

    logger.info(f"\nExported {5} JSON files to {output_dir}")
    logger.info("  - summary.json (key metrics)")
    logger.info("  - timeseries.json (monthly/annual charts)")
    logger.info("  - spatial.json (map data)")
    logger.info("  - states.json (state-level details)")
    logger.info("  - counties.json (county-level GeoJSON)")


def _export_counties(results: dict, output_dir: Path):
    """
    Build and write ``counties.json`` as a GeoJSON FeatureCollection.

    For each county, averages the TWS trend (cm/year) across the 0.5-degree
    grid cells that fall within the county's bounding box.  Classifies
    water stress using the same thresholds as the state-level analysis:

        - *severe*:   TWS trend < -1.5 cm/year
        - *moderate*: TWS trend < -0.5 cm/year
        - *stable*:   TWS trend >= -0.5 cm/year
    """
    counties = load_county_data()
    tws_trend_grid = np.array(results["spatial"]["tws_trend"])

    features = []
    for county in counties:
        grid_cells = county["grid_cells"]

        if grid_cells:
            # Average TWS trend across grid cells covered by this county
            cell_values = [
                tws_trend_grid[i, j]
                for i, j in grid_cells
                if i < tws_trend_grid.shape[0] and j < tws_trend_grid.shape[1]
            ]
            valid = [v for v in cell_values if np.isfinite(v)]
            tws_trend = round(float(np.mean(valid)), 2) if valid else 0.0
        else:
            tws_trend = 0.0

        # Water stress classification
        if tws_trend < -1.5:
            stress = "severe"
        elif tws_trend < -0.5:
            stress = "moderate"
        else:
            stress = "stable"

        feature = {
            "type": "Feature",
            "properties": {
                "name": county["name"],
                "state": county["state"],
                "fips": county["fips"],
                "tws_trend": tws_trend,
                "water_stress": stress,
                "population": county["population"],
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": county["polygon_coords"],
            },
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }
    _write_json(geojson, output_dir / "counties.json")

    # Log summary statistics
    stress_counts = {"severe": 0, "moderate": 0, "stable": 0}
    for f in features:
        stress_counts[f["properties"]["water_stress"]] += 1
    logger.info(
        f"  County stress: {stress_counts['severe']} severe, "
        f"{stress_counts['moderate']} moderate, "
        f"{stress_counts['stable']} stable"
    )


def _write_json(data: dict, filepath: Path):
    """Write dict to *filepath* as compact (no-whitespace) JSON."""
    with open(filepath, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    size_kb = filepath.stat().st_size / 1024
    logger.info(f"  Wrote {filepath.name} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    export_for_frontend()
