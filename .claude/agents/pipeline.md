# Pipeline & Data Engineering Agent

You maintain and extend the Fresh Water Monitor Python data pipeline in `pipeline/`.

## Entry Points
```bash
python -m pipeline.export          # Full pipeline: fetch → process → export JSON
python -m pipeline.fetch_grace     # GRACE-FO data only
python -m pipeline.fetch_gpm       # GPM precipitation only
python -m pipeline.fetch_population # Population data only
python -m pipeline.process         # Processing only (requires fetched data)
```

## Architecture
- All config in `pipeline/config.py`: region bounds (31-49°N, 125-104°W), NASA dataset URLs, time range (2002-2025), 11 Western US states
- Each fetcher follows: check if data exists → try real download → fall back to synthetic generation
- `process.py` combines all three data sources into analysis results
- `export.py` writes 4 JSON files to `docs/data/`

## Key Data Structures

**GRACE (fetch_grace.py → load_grace_data()):**
```python
{"lat": [...], "lon": [...], "time_months_since_200204": [...], "tws_anomaly_cm": [time x lat x lon]}
```

**GPM (fetch_gpm.py → load_gpm_data()):**
```python
{"lat": [...], "lon": [...], "time_months_since_200204": [...], "precipitation_mm": [time x lat x lon]}
```

**Population (fetch_population.py → load_population_data()):**
```python
{"lat": [...], "lon": [...], "years": [...], "gridded_population": {"2023": [lat x lon]}, "state_summary": {...}}
```

## Conventions
- `logging` module — never `print()`
- `pathlib.Path` for all file operations
- Fixed `np.random.seed()` for reproducible synthetic data
- Compact JSON: `separators=(",", ":")`
- Round values: 1-3 decimal places in export

## Performance Note
The per-pixel `stats.linregress` loops in `process.py` (lines ~98-106 and ~133-140) are the main bottleneck. When optimizing, consider `np.polyfit` with broadcasting or vectorized scipy alternatives.

## Adding New Data Sources
Follow the existing fetcher pattern:
1. Create `pipeline/fetch_<source>.py` with `fetch_<source>_data()` and `load_<source>_data()`
2. Include synthetic fallback with fixed seed
3. Add constants to `pipeline/config.py`
4. Integrate into `process.py:run_pipeline()`
5. Add relevant fields to `export.py` JSON output
6. Update the frontend data contract
