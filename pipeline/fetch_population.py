"""
Fetch population data for human impact analysis.

Uses a combination of US Census state-level data and approximate
spatial distribution for the United States.

Data sources:
- US Census Bureau (free, public domain)
- WorldPop (free, for future gridded population upgrades)
"""

import json
import logging
from pathlib import Path

import numpy as np

from pipeline.config import RAW_DIR, REGION

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# All 50 US state populations (2023 Census estimates)
STATE_POPULATIONS = {
    "Alabama": {"pop_2023": 5_108_468, "center_lat": 32.8, "center_lon": -86.8},
    "Alaska": {"pop_2023": 733_536, "center_lat": 64.2, "center_lon": -152.5},
    "Arizona": {"pop_2023": 7_431_344, "center_lat": 34.0, "center_lon": -111.1},
    "Arkansas": {"pop_2023": 3_067_732, "center_lat": 34.8, "center_lon": -92.2},
    "California": {"pop_2023": 38_965_193, "center_lat": 36.8, "center_lon": -119.4},
    "Colorado": {"pop_2023": 5_877_610, "center_lat": 39.0, "center_lon": -105.5},
    "Connecticut": {"pop_2023": 3_617_176, "center_lat": 41.6, "center_lon": -72.7},
    "Delaware": {"pop_2023": 1_031_890, "center_lat": 39.0, "center_lon": -75.5},
    "Florida": {"pop_2023": 22_610_726, "center_lat": 28.1, "center_lon": -81.6},
    "Georgia": {"pop_2023": 11_029_227, "center_lat": 33.0, "center_lon": -83.5},
    "Hawaii": {"pop_2023": 1_435_138, "center_lat": 20.8, "center_lon": -156.3},
    "Idaho": {"pop_2023": 1_964_726, "center_lat": 44.1, "center_lon": -114.7},
    "Illinois": {"pop_2023": 12_549_689, "center_lat": 40.0, "center_lon": -89.2},
    "Indiana": {"pop_2023": 6_862_199, "center_lat": 39.8, "center_lon": -86.1},
    "Iowa": {"pop_2023": 3_207_004, "center_lat": 42.0, "center_lon": -93.5},
    "Kansas": {"pop_2023": 2_940_546, "center_lat": 38.5, "center_lon": -98.3},
    "Kentucky": {"pop_2023": 4_526_154, "center_lat": 37.8, "center_lon": -84.3},
    "Louisiana": {"pop_2023": 4_573_749, "center_lat": 31.0, "center_lon": -92.0},
    "Maine": {"pop_2023": 1_395_722, "center_lat": 45.3, "center_lon": -69.0},
    "Maryland": {"pop_2023": 6_180_253, "center_lat": 39.0, "center_lon": -76.6},
    "Massachusetts": {"pop_2023": 7_001_399, "center_lat": 42.4, "center_lon": -71.4},
    "Michigan": {"pop_2023": 10_037_261, "center_lat": 44.3, "center_lon": -84.5},
    "Minnesota": {"pop_2023": 5_737_915, "center_lat": 46.3, "center_lon": -94.3},
    "Mississippi": {"pop_2023": 2_939_690, "center_lat": 32.7, "center_lon": -89.7},
    "Missouri": {"pop_2023": 6_196_156, "center_lat": 38.5, "center_lon": -92.3},
    "Montana": {"pop_2023": 1_132_812, "center_lat": 46.8, "center_lon": -110.4},
    "Nebraska": {"pop_2023": 1_978_379, "center_lat": 41.5, "center_lon": -99.8},
    "Nevada": {"pop_2023": 3_194_176, "center_lat": 38.8, "center_lon": -116.4},
    "New Hampshire": {"pop_2023": 1_402_054, "center_lat": 43.7, "center_lon": -71.5},
    "New Jersey": {"pop_2023": 9_290_841, "center_lat": 40.1, "center_lon": -74.7},
    "New Mexico": {"pop_2023": 2_114_371, "center_lat": 34.5, "center_lon": -106.2},
    "New York": {"pop_2023": 19_571_216, "center_lat": 42.2, "center_lon": -74.9},
    "North Carolina": {"pop_2023": 10_835_491, "center_lat": 35.6, "center_lon": -79.8},
    "North Dakota": {"pop_2023": 783_926, "center_lat": 47.5, "center_lon": -100.5},
    "Ohio": {"pop_2023": 11_785_935, "center_lat": 40.4, "center_lon": -82.8},
    "Oklahoma": {"pop_2023": 4_053_824, "center_lat": 35.5, "center_lon": -97.5},
    "Oregon": {"pop_2023": 4_233_358, "center_lat": 43.8, "center_lon": -120.6},
    "Pennsylvania": {"pop_2023": 12_961_683, "center_lat": 41.2, "center_lon": -77.2},
    "Rhode Island": {"pop_2023": 1_095_962, "center_lat": 41.7, "center_lon": -71.5},
    "South Carolina": {"pop_2023": 5_373_555, "center_lat": 34.0, "center_lon": -81.0},
    "South Dakota": {"pop_2023": 919_318, "center_lat": 44.2, "center_lon": -100.2},
    "Tennessee": {"pop_2023": 7_126_489, "center_lat": 35.8, "center_lon": -86.4},
    "Texas": {"pop_2023": 30_503_301, "center_lat": 31.5, "center_lon": -99.0},
    "Utah": {"pop_2023": 3_417_734, "center_lat": 39.3, "center_lon": -111.7},
    "Vermont": {"pop_2023": 647_464, "center_lat": 44.0, "center_lon": -72.7},
    "Virginia": {"pop_2023": 8_715_698, "center_lat": 37.4, "center_lon": -78.7},
    "Washington": {"pop_2023": 7_812_880, "center_lat": 47.4, "center_lon": -120.7},
    "West Virginia": {"pop_2023": 1_770_071, "center_lat": 38.6, "center_lon": -80.6},
    "Wisconsin": {"pop_2023": 5_910_955, "center_lat": 44.6, "center_lon": -90.0},
    "Wyoming": {"pop_2023": 584_057, "center_lat": 43.0, "center_lon": -107.6},
}

# Historical population growth rates (approximate annual % growth)
GROWTH_RATES = {
    "Alabama": 0.3,
    "Alaska": 0.2,
    "Arizona": 1.6,
    "Arkansas": 0.3,
    "California": 0.2,
    "Colorado": 1.4,
    "Connecticut": 0.1,
    "Delaware": 0.9,
    "Florida": 1.6,
    "Georgia": 1.0,
    "Hawaii": 0.3,
    "Idaho": 2.1,
    "Illinois": -0.3,
    "Indiana": 0.3,
    "Iowa": 0.3,
    "Kansas": 0.2,
    "Kentucky": 0.3,
    "Louisiana": -0.1,
    "Maine": 0.3,
    "Maryland": 0.5,
    "Massachusetts": 0.5,
    "Michigan": 0.1,
    "Minnesota": 0.7,
    "Mississippi": -0.2,
    "Missouri": 0.2,
    "Montana": 1.5,
    "Nebraska": 0.6,
    "Nevada": 1.8,
    "New Hampshire": 0.5,
    "New Jersey": 0.3,
    "New Mexico": 0.4,
    "New York": -0.2,
    "North Carolina": 1.1,
    "North Dakota": 1.0,
    "Ohio": 0.0,
    "Oklahoma": 0.5,
    "Oregon": 1.2,
    "Pennsylvania": 0.0,
    "Rhode Island": 0.2,
    "South Carolina": 1.3,
    "South Dakota": 1.1,
    "Tennessee": 0.9,
    "Texas": 1.7,
    "Utah": 1.7,
    "Vermont": 0.1,
    "Virginia": 0.7,
    "Washington": 1.5,
    "West Virginia": -0.5,
    "Wisconsin": 0.3,
    "Wyoming": 0.3,
}


def generate_population_data(output_dir: Path = RAW_DIR) -> Path:
    """
    Generate gridded population data for the United States.

    Creates a spatial population distribution by placing each state's
    population around its census-derived center using a Gaussian kernel
    (sigma scales with log10 of population).  Historical yearly grids
    are back-projected from 2023 estimates using ``GROWTH_RATES``.

    The output grid matches GRACE/GPM resolution (0.5 degrees) so the
    three datasets can be combined pixel-by-pixel in
    :func:`pipeline.process.compute_impact_metrics`.

    Args:
        output_dir: Directory to save the population JSON file.

    Returns:
        Path to the generated ``population.json`` file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "population.json"

    if output_path.exists():
        logger.info(f"Population data already exists at {output_path}")
        return output_path

    logger.info("Generating United States population data...")

    # Grid matching GRACE/GPM resolution
    lats = np.arange(REGION["min_lat"], REGION["max_lat"] + 0.5, 0.5)
    lons = np.arange(REGION["min_lon"], REGION["max_lon"] + 0.5, 0.5)
    n_lat, n_lon = len(lats), len(lons)

    lat_grid, lon_grid = np.meshgrid(lats, lons, indexing="ij")

    # Approximate spatial population distribution using Gaussian kernels.
    # Each state's total Census population is spread as a bell curve centered
    # on its population center. The kernel width (sigma) scales with
    # log10(population), so large states spread wider. The kernel is normalized
    # so the grid total matches the Census count exactly. This is a
    # simplification (real population clusters in cities), but is sufficient
    # for regional water-stress overlay at the 0.5-degree grid scale.
    # A future upgrade could use WorldPop 1km gridded data instead.
    pop_grid = np.zeros((n_lat, n_lon))

    for _state, info in STATE_POPULATIONS.items():
        # Distance from state center (in degrees, rough approximation)
        dist = np.sqrt((lat_grid - info["center_lat"]) ** 2 + (lon_grid - info["center_lon"]) ** 2)

        # Gaussian kernel width: base 1.5 deg + log-scaled term.
        # CA (39M) -> sigma ~3.8 deg (~400 km); WY (584K) -> sigma ~3.2 deg
        sigma = 1.5 + np.log10(info["pop_2023"]) * 0.3
        kernel = np.exp(-(dist**2) / (2 * sigma**2))

        # Normalize so total matches state population
        kernel_sum = kernel.sum()
        if kernel_sum > 0:
            pop_grid += info["pop_2023"] * kernel / kernel_sum

    # Generate historical population for multiple years
    years = list(range(2002, 2025))
    yearly_data = {}

    for year in years:
        year_offset = year - 2023
        year_grid = np.zeros((n_lat, n_lon))

        for state, info in STATE_POPULATIONS.items():
            growth_rate = GROWTH_RATES[state] / 100.0
            adjusted_pop = info["pop_2023"] * (1 + growth_rate) ** year_offset

            dist = np.sqrt(
                (lat_grid - info["center_lat"]) ** 2 + (lon_grid - info["center_lon"]) ** 2
            )
            sigma = 1.5 + np.log10(info["pop_2023"]) * 0.3
            kernel = np.exp(-(dist**2) / (2 * sigma**2))

            kernel_sum = kernel.sum()
            if kernel_sum > 0:
                year_grid += adjusted_pop * kernel / kernel_sum

        yearly_data[str(year)] = year_grid.tolist()

    # State-level summary
    state_summary = {}
    for state, info in STATE_POPULATIONS.items():
        state_summary[state] = {
            "population_2023": info["pop_2023"],
            "center_lat": info["center_lat"],
            "center_lon": info["center_lon"],
            "annual_growth_pct": GROWTH_RATES[state],
        }

    result = {
        "lat": lats.tolist(),
        "lon": lons.tolist(),
        "years": years,
        "gridded_population": yearly_data,
        "state_summary": state_summary,
        "total_population_2023": sum(s["pop_2023"] for s in STATE_POPULATIONS.values()),
    }

    with open(output_path, "w") as f:
        json.dump(result, f)

    logger.info(f"Population data saved to {output_path}")
    logger.info(f"Total United States population (2023): {result['total_population_2023']:,}")
    return output_path


def load_population_data(filepath: Path | None = None) -> dict:
    """
    Load population data from the JSON file.

    Args:
        filepath: Path to a population JSON file.  When *None*, looks
            in ``RAW_DIR`` and generates automatically if missing.

    Returns:
        Dict with keys:
            - ``"lat"`` (list[float]): Latitude values (degrees north).
            - ``"lon"`` (list[float]): Longitude values (degrees east).
            - ``"years"`` (list[int]): Years with population grids (2002-2024).
            - ``"gridded_population"`` (dict[str, list]): Year-keyed
              population grids, each [lat x lon] (persons per cell).
            - ``"state_summary"`` (dict): Per-state population, center
              coordinates (degrees), and annual growth rate (%).
            - ``"total_population_2023"`` (int): Sum across all 50 states.
    """
    if filepath is None:
        filepath = RAW_DIR / "population.json"

    if not filepath.exists():
        filepath = generate_population_data()

    with open(filepath) as f:
        return json.load(f)


if __name__ == "__main__":
    filepath = generate_population_data()
    data = load_population_data(filepath)
    logger.info(
        f"Loaded population data: "
        f"{len(data['lat'])} lats x {len(data['lon'])} lons, "
        f"{len(data['years'])} years"
    )
