# Fresh Water Monitor

Satellite-based freshwater monitoring for the United States. Combines GRACE-FO terrestrial water storage, GPM precipitation, and US Census population data to show how water availability is changing and what that means for people in affected regions.

Deployed as a static [GitHub Pages dashboard](https://promeos.github.io/fresh-water/).

## Prerequisites

- Python 3.11+
- A [NASA Earthdata](https://urs.earthdata.nasa.gov/) account (free — needed for live satellite data)

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

Live satellite data requires a NASA Earthdata API token. Without it, the pipeline uses synthetic fallback data — perfectly fine for development and exploring the dashboard.

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
fetch_gpm.py ────┼─→ process.py ─→ export.py ─→ docs/data/*.json ─→ dashboard
fetch_population ┘
```

Each fetcher has a synthetic fallback — no NASA Earthdata credentials are needed for development.

## Data Sources & Attribution

This project uses publicly available satellite and demographic datasets:

| Dataset | Provider | Description |
|---------|----------|-------------|
| [GRACE/GRACE-FO Mascon RL06.1 V3](https://podaac.jpl.nasa.gov/) | NASA JPL / GFZ | Terrestrial water storage anomalies |
| [GPM IMERG V07](https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGM_07/summary) | NASA GES DISC | Monthly precipitation estimates |
| [US Census Bureau](https://www.census.gov/) | US Census Bureau | State-level population data |
| [WorldPop](https://www.worldpop.org/) | WorldPop / University of Southampton | Gridded population estimates |

### Copernicus Sentinel Data

This project contains modified Copernicus Sentinel data (2002–2025). Access and use of Copernicus Sentinel Data is regulated under [EU Regulation No 1159/2013](https://eur-lex.europa.eu/eli/reg_del/2013/1159/oj) and is provided free, full, and open under the [Copernicus Sentinel Data Terms](https://sentinels.copernicus.eu/web/sentinel/terms-conditions).

### NASA GES DISC

Data retrieved from the NASA Goddard Earth Sciences Data and Information Services Center (GES DISC) are subject to the [NASA GES DISC Data Policy](https://disc.gsfc.nasa.gov/information/documents?title=data-policy). Users must register with [NASA Earthdata Login](https://urs.earthdata.nasa.gov/).

## Disclaimer

Data presented in this dashboard is derived from publicly available satellite observations and is provided **for informational and educational purposes only**. It comes with no warranty of quality or fitness for any purpose. Do not use this data as the sole basis for policy, planning, or operational decisions.

## License

This project is licensed under [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/). You are free to share and adapt the work as long as you give appropriate credit. See [CITATION.cff](CITATION.cff) for citation information.
