"""
Configuration for the Fresh Water monitoring pipeline.

Centralizes credentials, file paths, geographic bounds, and dataset
identifiers used by every stage of the pipeline.  Constants here are
intentionally module-level so they can be imported directly
(``from pipeline.config import REGION``).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# NASA Earthdata credentials (set via .env or environment variables)
EARTHDATA_USERNAME = os.getenv("EARTHDATA_USERNAME", "Promeos")
NASA_API_KEY = os.getenv("NASA_API_KEY", "")

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "docs" / "data"
RAW_DIR = PROJECT_ROOT / "pipeline" / "raw_data"

# Contiguous US bounding box (degrees).
# Covers all 48 contiguous states from the southern tip of Texas (~24 N)
# to the Canadian border (~50 N) and coast to coast (~125 W to ~66 W).
REGION = {
    "name": "United States",
    "min_lat": 24.0,  # degrees north (southern FL/TX)
    "max_lat": 50.0,  # degrees north (Canadian border)
    "min_lon": -125.0,  # degrees east (Pacific coast)
    "max_lon": -66.0,  # degrees east (Atlantic coast, ME)
}

# All 50 US states
STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California",
    "Colorado", "Connecticut", "Delaware", "Florida", "Georgia",
    "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
    "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland",
    "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri",
    "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey",
    "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
    "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina",
    "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
    "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming",
]

# GRACE-FO settings -- RL06.1 V3 Mascon CRI is the latest publicly
# available release as of early 2026.
GRACE_DATASET = "TELLUS_GRAC-GRFO_MASCON_CRI_GRID_RL06.1_V3"
GRACE_BASE_URL = (
    "https://podaac-tools.jpl.nasa.gov/drive/files/allData/tellus/L3/mascon/RL06.1/JPL/CRI/netcdf"
)

# GPM IMERG settings (monthly, Final Run, Version 07)
GPM_BASE_URL = "https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGM_07/summary"

# Population data (WorldPop)
WORLDPOP_BASE_URL = "https://data.worldpop.org/GIS/Population/Global_2000_2020_1km"

# Time range -- GRACE launched April 2002; END_YEAR is inclusive.
START_YEAR = 2002
END_YEAR = 2025
