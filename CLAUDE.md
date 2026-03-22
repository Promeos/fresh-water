# Fresh Water Monitor

Satellite-based freshwater monitoring for the Western US. Combines GRACE-FO terrestrial water storage, GPM precipitation, and US Census population data to show how water availability is changing and what that means for people in affected regions. Deployed as a static GitHub Pages dashboard.

## Architecture

```
fresh-water/
  pipeline/               # Python data pipeline
    config.py             # Region bounds, dataset URLs, time range (2002-2025), state list
    fetch_grace.py        # GRACE-FO TWS anomaly data (NetCDF, synthetic fallback)
    fetch_gpm.py          # GPM IMERG precipitation data (NetCDF, synthetic fallback)
    fetch_population.py   # Population grid + state summary (Gaussian spatial distribution)
    process.py            # Statistical analysis: area-weighted averages, linear trends, human impact
    export.py             # Exports 4 JSON files to docs/data/
  docs/                   # GitHub Pages frontend (static site)
    index.html            # Dashboard HTML
    css/style.css         # Dark theme design system (CSS custom properties)
    js/dashboard.js       # Chart rendering, data loading, state table
    data/                 # Pipeline JSON output (summary, timeseries, spatial, states)
  .github/workflows/      # CI/CD
  tests/                  # pytest test suite
  requirements.txt        # numpy, pandas, xarray, netCDF4, h5py, requests, plotly, scipy
```

## Commands

```bash
pip install -r requirements.txt           # Install dependencies
python -m pipeline.export                 # Run full pipeline (fetch + process + export JSON)
python -m http.server 8000 --directory docs  # Serve frontend locally at localhost:8000
python -m pytest tests/ -v                # Run tests
```

Individual pipeline stages:
```bash
python -m pipeline.fetch_grace            # Fetch/generate GRACE data only
python -m pipeline.fetch_gpm              # Fetch/generate GPM data only
python -m pipeline.fetch_population       # Generate population data only
python -m pipeline.process                # Run processing only (requires fetched data)
```

## Data Flow

```
fetch_grace.py ──┐
fetch_gpm.py ────┼─→ process.py ─→ export.py ─→ docs/data/*.json ─→ frontend renders
fetch_population ┘
```

Pipeline outputs 4 JSON files to `docs/data/`:
- **summary.json** — Headline metrics and metadata (loaded first by frontend)
- **timeseries.json** — Monthly/annual TWS and precipitation arrays
- **spatial.json** — Lat/lon grids with TWS trend and precipitation change
- **states.json** — Per-state population, trends, stress classification, sparkline timeseries

## Code Conventions

### Python (pipeline/)
- Module-level docstrings explaining data source and purpose
- `logging` module for output — never `print()`
- `pathlib.Path` for all file paths
- Fixed `np.random.seed()` for reproducible synthetic data
- Shared constants imported from `pipeline.config`
- Compact JSON: `json.dump(data, f, separators=(",", ":"))`
- Values rounded to 1-3 decimal places in export

### Frontend (docs/)
- Vanilla JS — no frameworks
- Plotly.js for all charts (loaded via CDN)
- CSS custom properties in `:root` for theming (dark theme)
- Inter font family
- Cards: `border-radius: 12px`, `border: 1px solid var(--border)`
- Responsive breakpoint at 768px

## Important Notes

- Each fetcher has a **synthetic fallback** — no NASA Earthdata credentials needed for development
- `docs/data/` is the bridge between pipeline and frontend: pipeline writes here, frontend reads
- The 11 Western US states are defined in `pipeline/config.py:STATES`
- Water stress thresholds: severe (< -1.5 cm/yr TWS decline), moderate (< -0.5), stable (>= -0.5)
- Grid resolution: 0.5 degrees over Western US bounding box (31-49°N, 125-104°W)
