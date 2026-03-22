# Fresh Water Monitor

Satellite-based freshwater monitoring for the United States. Combines GRACE-FO terrestrial water storage, GPM precipitation, and US Census population data to show how water availability is changing and what that means for people in affected regions.

Deployed as a static [GitHub Pages dashboard](https://promeos.github.io/fresh-water/).

## Quick Start

```bash
pip install -r requirements.txt
python -m pipeline.export            # Run full pipeline (fetch + process + export)
python -m http.server 8000 --directory docs  # Serve dashboard at localhost:8000
python -m pytest tests/ -v           # Run tests
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
