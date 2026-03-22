# Fresh Water Monitor

Satellite-based freshwater monitoring for the United States. Combines NASA GRACE-FO terrestrial water storage (TWS), GPM IMERG precipitation, and US Census population data to show how water availability is changing and what that means for people in affected regions.

**[View the live dashboard](https://promeos.github.io/fresh-water/)**

## What This Project Does

Fresh Water Monitor tracks underground and surface water changes across all 50 US states using satellite measurements from NASA's GRACE-FO mission. It answers three questions:

1. **Where is water disappearing?** Per-county water storage trends mapped from satellite gravimetry data (2002--present).
2. **How severe is the decline?** Regions classified as *stable*, *moderate*, or *severe* based on long-term trends.
3. **How many people are affected?** Population overlays estimate how many people live in areas of declining water storage.

## Key Metrics

| Metric | What It Measures | How to Read It |
|--------|-----------------|----------------|
| **TWS Anomaly (cm)** | How much water storage deviates from the 2004--2009 baseline | Negative = less water than the historical average |
| **TWS Trend (cm/year)** | Rate of water storage change over the satellite record | Below -0.5 = declining; below -1.5 = severe |
| **Precipitation Deficit (%)** | Recent 3-year average vs. historical average rainfall | Negative = drier than normal |
| **Population Affected** | People in grid cells where TWS trend < -0.5 cm/year | Higher = more people exposed to water stress |
| **Water Stress** | Classification per region | Severe (< -1.5 cm/yr), Moderate (< -0.5), Stable (>= -0.5) |

## Prerequisites

- Python 3.11+
- A [NASA Earthdata](https://urs.earthdata.nasa.gov/) account (free -- needed for live satellite data, optional for development)

## Setup

### 1. Clone and install

```bash
git clone https://github.com/Promeos/fresh-water.git
cd fresh-water
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure credentials (optional)

Live satellite data requires a NASA Earthdata API token. Without it, the pipeline uses synthetic fallback data -- perfectly fine for development and exploring the dashboard.

To use real data:

1. Create a free account at [NASA Earthdata Login](https://urs.earthdata.nasa.gov/)
2. Go to **My Profile > Generate Token** to get an API key
3. Create a `.env` file in the project root:

```bash
EARTHDATA_USERNAME='your_username'
NASA_API_KEY='your_api_token'
```

> Tokens expire periodically. If fetches start failing, generate a new token from your Earthdata profile.

### 3. Run the pipeline

```bash
python -m pipeline.export            # Fetch data, process, and export JSON to docs/data/
```

This runs the full pipeline: fetch GRACE-FO + GPM + population data, compute trends and statistics, and write JSON files to `docs/data/`.

You can also run individual stages:

```bash
python -m pipeline.fetch_grace       # Fetch GRACE-FO water storage data
python -m pipeline.fetch_gpm         # Fetch GPM precipitation data
python -m pipeline.fetch_population  # Generate population grid
python -m pipeline.process           # Process all fetched data
```

### 4. View the dashboard

```bash
python -m http.server 8000 --directory docs
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

### 5. Run tests

```bash
pip install -r requirements-dev.txt  # Install test dependencies (pytest, ruff)
python -m pytest tests/ -v
```

## Architecture

```
pipeline/          Python data pipeline (fetch, process, export)
docs/              GitHub Pages frontend (static dashboard)
  data/            Pipeline JSON output consumed by the frontend
tests/             pytest suite
```

### Data Flow

```
fetch_grace.py ──┐
fetch_gpm.py ────┼--> process.py --> export.py --> docs/data/*.json --> dashboard
fetch_population ┘
```

Each fetcher has a synthetic fallback -- no NASA Earthdata credentials are needed for development.

## Data Sources

| Dataset | Full Name | Provider | Resolution | Coverage |
|---------|-----------|----------|------------|----------|
| [GRACE-FO Mascon RL06.1 V3](https://podaac.jpl.nasa.gov/) | Gravity Recovery and Climate Experiment Follow-On | NASA JPL / GFZ | Monthly, ~300 km (mascon tiles) | Apr 2002--present |
| [GPM IMERG V07](https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGM_07/summary) | Global Precipitation Measurement Integrated Multi-satellite Retrievals | NASA GES DISC | Monthly, 0.1 degree (~10 km) | Jun 2000--present |
| [US Census Bureau](https://www.census.gov/) | Population Estimates Program | Census Bureau | Annual, state-level | 2000--2023 |
| [WorldPop](https://www.worldpop.org/) | Gridded Population Estimates | University of Southampton | 1 km | 2000--2020 |

### Copernicus Sentinel Data

This project contains modified Copernicus Sentinel data (2002--2025). Access and use of Copernicus Sentinel Data is regulated under [EU Regulation No 1159/2013](https://eur-lex.europa.eu/eli/reg_del/2013/1159/oj) and is provided free, full, and open under the [Copernicus Sentinel Data Terms](https://sentinels.copernicus.eu/web/sentinel/terms-conditions).

### NASA GES DISC

Data retrieved from the NASA Goddard Earth Sciences Data and Information Services Center (GES DISC) are subject to the [NASA GES DISC Data Policy](https://disc.gsfc.nasa.gov/information/documents?title=data-policy). Users must register with [NASA Earthdata Login](https://urs.earthdata.nasa.gov/).

## Glossary

| Term | Definition |
|------|------------|
| **TWS** | Terrestrial Water Storage -- total water on and below the land surface (groundwater, soil moisture, snow, surface water) |
| **GRACE-FO** | Gravity Recovery and Climate Experiment Follow-On -- twin satellites that detect gravity changes caused by shifting water mass |
| **Mascon** | Mass Concentration block -- a tile on Earth's surface (~300 km) used to estimate local gravity and water changes from GRACE data |
| **IMERG** | Integrated Multi-satellite Retrievals for GPM -- algorithm that merges data from multiple precipitation-measuring satellites |
| **LWE** | Liquid Water Equivalent -- expressing water volume as a uniform layer of water in centimeters |
| **Anomaly** | Difference from a reference average; here, deviation from the 2004--2009 baseline period |
| **CRI** | Coastline Resolution Improvement -- a filter applied to GRACE mascon data to reduce signal leakage near coastlines |

## Citation

If you use this project in research or publications, please cite it:

```bibtex
@software{fresh_water_monitor,
  title = {Fresh Water Monitor},
  author = {Promeos},
  url = {https://github.com/Promeos/fresh-water},
  version = {1.0.0},
  date = {2026-03-22},
  license = {CC-BY-4.0}
}
```

Full citation metadata is available in [CITATION.cff](CITATION.cff), which is automatically recognized by GitHub and Zenodo.

## Disclaimer

Data presented in this dashboard is derived from publicly available satellite observations and is provided **for informational and educational purposes only**. It comes with no warranty of quality or fitness for any purpose. Do not use this data as the sole basis for policy, planning, or operational decisions.

## License

This project is licensed under [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/). You are free to share and adapt the work as long as you give appropriate credit. See [CITATION.cff](CITATION.cff) for citation information.
