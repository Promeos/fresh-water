---
name: run-pipeline
description: Run the full Fresh Water Monitor data pipeline (fetch, process, export) and verify outputs
---

# Run Pipeline

Execute the full data pipeline and verify the outputs.

## Steps

1. Install dependencies if needed:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the full pipeline (fetch → process → export):
   ```bash
   python -m pipeline.export
   ```

3. Verify all 4 JSON output files exist and are valid:
   - `docs/data/summary.json`
   - `docs/data/timeseries.json`
   - `docs/data/spatial.json`
   - `docs/data/states.json`

4. Report the key metrics from the pipeline output:
   - TWS trend (cm/year)
   - Population affected by water decline
   - Number of states in severe/moderate/stable stress

5. If the user passes arguments like "serve" or "preview", also start the local server:
   ```bash
   python -m http.server 8000 --directory docs
   ```
