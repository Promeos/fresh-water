# README Agent

You create and maintain the project README.md for the Fresh Water Monitor.

## Target File
`README.md` at the project root (`/Users/christopherortiz/Desktop/fresh-water/README.md`)

## Structure

### Required Sections
1. **Title + Badge Row** — Project name, Python version badge, license badge, GitHub Pages status badge
2. **One-Line Description** — "Satellite-based freshwater monitoring dashboard for the Western US"
3. **Screenshot** — Dashboard screenshot (after frontend is built). Use relative path: `docs/assets/screenshot.png`
4. **Live Demo** — Link to GitHub Pages deployment
5. **Quick Start** — Clone, install, run pipeline, serve locally (4 commands max)
6. **What This Shows** — Plain-language explanation of the dashboard for non-technical users
7. **Data Sources** — Table with source name, provider, what it measures, and link
8. **Architecture** — Text-based diagram of the data flow (fetch → process → export → frontend)
9. **Project Structure** — Directory tree with one-line descriptions
10. **Development** — How to add data sources, run tests, lint
11. **License** — MIT

## Tone
- Accessible to non-experts — this is meant to democratize water data
- Lead with *what the user sees* (the dashboard), not implementation details
- Technical depth increases as you go down the README
- Use plain language for the top half, developer language for the bottom half

## Data Sources Table

| Source | Measures | Provider | Link |
|--------|----------|----------|------|
| GRACE-FO | Terrestrial water storage changes | NASA JPL | podaac.jpl.nasa.gov |
| GPM IMERG | Monthly precipitation | NASA GES DISC | gpm.nasa.gov |
| US Census | Population by state | Census Bureau | census.gov |

## Quick Start Template
```bash
git clone <repo-url>
cd fresh-water
pip install -r requirements.txt
python -m pipeline.export
python -m http.server 8000 --directory docs
# Open http://localhost:8000
```

## Key Facts to Include
- Covers 11 Western US states (WA, OR, CA, NV, ID, MT, WY, UT, CO, AZ, NM)
- Data from 2002 to present
- Pipeline has synthetic fallback — works without NASA credentials for development
- Frontend is pure static HTML/CSS/JS — no build step, no server needed
- Deployed via GitHub Pages from `docs/` directory

## After Creating
- Verify all relative links work
- Ensure commands in Quick Start actually run successfully
- Check that badge URLs are correct once the repo is pushed
