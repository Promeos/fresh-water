# Testing & Validation Agent

You write and maintain tests for the Fresh Water Monitor project.

## Setup
- Framework: pytest (add to `requirements.txt` if missing)
- Test directory: `tests/` at project root
- Run: `python -m pytest tests/ -v`
- All tests must work with synthetic data — no NASA credentials required

## Test Structure

```
tests/
  conftest.py                    # Shared fixtures (pipeline results, tmp output dir)
  test_pipeline/
    test_config.py               # Config values are reasonable
    test_fetch_grace.py          # Synthetic GRACE data shape, ranges, no NaN
    test_fetch_gpm.py            # Synthetic GPM data non-negative, correct grid
    test_fetch_population.py     # Population positive, state list complete
    test_process.py              # Timeseries, spatial trends, impact metrics
    test_export.py               # JSON output keys, valid JSON, rounded values
  test_integration.py            # Full pipeline produces all 4 JSON files
  test_data_quality.py           # Range checks, NaN checks, format validation
```

## Unit Test Targets

**test_config.py:** Lat/lon bounds valid, year range sensible, 11 states listed

**test_fetch_grace.py:** Output dict has required keys (`lat`, `lon`, `time_months_since_200204`, `tws_anomaly_cm`), grid shape matches region, no NaN values

**test_fetch_gpm.py:** Precipitation values non-negative, correct grid dimensions, time axis matches GRACE

**test_fetch_population.py:** Population values positive, total reasonable (millions), all 11 states in state_summary

**test_process.py:**
- `months_since_200204_to_dates()` — known inputs produce correct YYYY-MM strings
- `compute_regional_timeseries()` — returns expected keys, trend is finite
- `compute_impact_metrics()` — stress classifications correct (severe < -1.5, moderate < -0.5, stable >= -0.5)

**test_export.py:** All 4 JSON files created, each is valid JSON, contains expected top-level keys

## Data Quality Checks (test_data_quality.py)
- TWS anomalies in range: -50 to 50 cm
- Precipitation: non-negative
- Population: positive integers
- No inf/NaN in any output JSON
- All dates match `YYYY-MM` format
- Lat/lon within region bounds (31-49°N, 125-104°W)

## Fixtures (conftest.py)
- `pipeline_results` — run `run_pipeline()` once per session (`scope="session"`)
- `export_dir` — `tmp_path` for JSON export testing
- `grace_data`, `gpm_data`, `pop_data` — individual dataset fixtures
