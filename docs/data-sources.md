# Data Sources & Dashboard Guide

**Last updated:** 2026-03-22

This document explains where the Fresh Water Monitor gets its data, what each metric means, and how to interpret the dashboard. No science background required.

---

## Data Sources

The dashboard combines three satellite and census datasets to paint a picture of freshwater availability across the United States (all 50 states).

| Dataset | What It Measures | Provider | How Often Updated | Spatial Detail | Time Coverage |
|---------|-----------------|----------|-------------------|----------------|---------------|
| **GRACE-FO** (Gravity Recovery and Climate Experiment Follow-On) | Total underground + surface water changes, measured by detecting tiny shifts in Earth's gravity from orbit | NASA Jet Propulsion Laboratory (JPL) | Monthly | ~300 km grid cells (mascon tiles) | Apr 2002 -- present |
| **GPM IMERG** (Global Precipitation Measurement, Integrated Multi-satellite Retrievals) | Rainfall and snowfall estimated from a constellation of satellites | NASA Goddard Earth Sciences (GES DISC) | Monthly | ~10 km (0.1 degree) | Jun 2000 -- present |
| **US Census Population Estimates** | State-level population counts, distributed spatially using a Gaussian approximation around population centers | US Census Bureau | Annual | State-level, gridded to ~50 km for this project | 2002 -- 2023 |

### How the data gets to the dashboard

```
NASA satellites --> NetCDF files --> Python pipeline --> JSON files --> Browser dashboard
```

1. **Fetch:** The pipeline downloads (or generates synthetic versions of) GRACE and GPM satellite data as NetCDF files, plus Census population data.
2. **Process:** Python computes trends, averages, and human impact metrics.
3. **Export:** Results are split into four JSON files optimized for fast loading.
4. **Display:** The browser dashboard reads those JSON files and renders charts with Plotly.js.

---

## Dashboard Metrics Explained

### Water Storage Anomaly (cm)

- **What it is:** How much the total water stored in a region (groundwater, soil moisture, snowpack, reservoirs, rivers) differs from a reference average. Measured in centimeters of "equivalent water thickness" -- imagine spreading all the water evenly across the land surface.
- **Baseline period:** 2004--2009 average (the standard GRACE reference period).
- **How to read it:**
  - **0 cm** = matches the baseline average
  - **Negative values** (e.g., -10 cm) = less water than the baseline -- the region is drier than normal
  - **Positive values** (e.g., +5 cm) = more water than the baseline -- wetter than normal
- **Why it matters:** This is the most comprehensive single measure of water availability. It captures water you can't see (deep underground) along with water you can (lakes, snow).

### Water Storage Trend (cm/year)

- **What it is:** The rate at which water storage is changing over the full record (2002--present), calculated by fitting a straight line through the monthly data.
- **How to read it:**
  - **>= -0.5 cm/year** = **Stable** -- water levels are roughly holding steady
  - **-0.5 to -1.5 cm/year** = **Moderate decline** -- water is being lost faster than it is replenished
  - **< -1.5 cm/year** = **Severe decline** -- a serious, sustained loss of water resources
- **On the map:** Red areas are losing water; blue areas are gaining. White is near zero change.

### Precipitation Deficit (%)

- **What it is:** How recent rainfall/snowfall (last 3 years) compares to the historical average for the full record.
- **How to read it:**
  - **0%** = recent precipitation matches the long-term average
  - **-20%** = the region has been getting 20% less rain/snow than normal
  - **+10%** = 10% wetter than normal
- **Why it matters:** Precipitation is the main input to the water cycle. Sustained deficits lead to drought, reduced reservoir levels, and declining groundwater.

### Population Affected

- **What it is:** The estimated number of people living in areas where water storage is declining (trend < -0.5 cm/year).
- **How it's calculated:** The pipeline overlays a population grid on the water trend map and sums up the population in each grid cell that shows a declining trend.
- **"Severe decline" subset:** People in grid cells where the trend is below -1.5 cm/year.

### Water Stress Classification (per state)

Each of the 50 US states is assigned a status based on the water storage trend at its population center:

| Status | TWS Trend Threshold | What It Means |
|--------|-------------------|---------------|
| **Stable** | >= -0.5 cm/year | Water supply is roughly in balance |
| **Moderate** | -0.5 to -1.5 cm/year | Noticeable decline; warrants monitoring |
| **Severe** | < -1.5 cm/year | Sustained, significant water loss |

---

## Technical Details

### Grid Resolution

All datasets are resampled to a common **0.5-degree grid** (~50 km) covering the contiguous US bounding box: 24--50 degrees North latitude, 125--66 degrees West longitude.

### Area-Weighted Averaging

When computing regional averages, each grid cell is weighted by the cosine of its latitude. This accounts for the fact that grid cells near the equator cover more area than grid cells near the poles. Without this correction, northern states would be over-represented.

### Synthetic Data Fallback

If the pipeline cannot download real NASA data (e.g., no internet or no Earthdata credentials), it generates **synthetic data** that mimics real patterns:

- Seasonal cycles (wet winters, dry summers)
- Long-term drought trends (matching known US droughts in 2011--2013, 2014--2017, 2020--2022)
- Spatial gradients (wetter in the Pacific Northwest, drier in the Desert Southwest)
- Random noise for realism

Synthetic data uses fixed random seeds (`np.random.seed(42)` for GRACE, `np.random.seed(123)` for GPM) so results are reproducible.

### Data File Formats

The pipeline outputs five JSON files to `docs/data/`:

| File | Contents | Typical Size |
|------|----------|-------------|
| `summary.json` | Headline metrics, metadata | ~1 KB |
| `timeseries.json` | Monthly and annual time series for charts | ~50 KB |
| `spatial.json` | Lat/lon grids for the heatmap | ~200 KB |
| `states.json` | Per-state impacts with sparkline data | ~100 KB |
| `counties.json` | GeoJSON with per-county TWS trend and water stress | ~500 KB |

---

## Further Reading

- [GRACE-FO Mission Overview](https://gracefo.jpl.nasa.gov/) -- NASA JPL
- [GPM IMERG Dataset Documentation](https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGM_07/summary) -- NASA GES DISC
- [US Census Population Estimates](https://www.census.gov/programs-surveys/popest.html) -- Census Bureau
- [WorldPop Global Population Data](https://www.worldpop.org/) -- for future gridded population upgrades
