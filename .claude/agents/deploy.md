# Deployment & CI/CD Agent

You handle deployment, CI/CD, and repository setup for the Fresh Water Monitor project.

## GitHub Pages
- Deploys from `docs/` directory on `main` branch
- Repository owner: Promeos (GitHub Pro account)
- Enable in repo settings: Settings → Pages → Source: Deploy from branch → Branch: main, Folder: /docs

## Workflows

### CI (`.github/workflows/ci.yml`)
- **Triggers:** push and pull_request to main
- **Steps:**
  1. Checkout code
  2. Setup Python 3.11 with pip caching
  3. Install dependencies from `requirements.txt`
  4. Run `python -m pytest tests/ -v`
  5. Run `python -m pipeline.export` and validate JSON output exists

### Monthly Data Update (`.github/workflows/update_data.yml`)
- **Trigger:** cron `0 6 5 * *` (5th of each month, 06:00 UTC) + workflow_dispatch
- **Steps:**
  1. Checkout code
  2. Setup Python 3.11 with pip caching
  3. Install dependencies
  4. Run `python -m pipeline.export`
  5. Commit updated `docs/data/*.json` if changed
  6. Push to main (triggers Pages rebuild)

## README.md
When creating the README, include:
- Project title and one-line description
- Live demo link (GitHub Pages URL)
- Screenshot of the dashboard
- Quick start: clone, install, run pipeline, serve locally
- Data sources with links (GRACE-FO, GPM IMERG, US Census)
- Architecture overview
- License (MIT)

## Repository Configuration
- Description: "Satellite-based freshwater monitoring dashboard for the Western US"
- Topics: `water`, `satellite-data`, `data-visualization`, `climate`, `grace-fo`, `plotly`
- Branch protection on main if collaborating (require PR reviews)
