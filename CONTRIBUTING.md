# Contributing to Fresh Water Monitor

Thanks for your interest in contributing! This project aims to make satellite-based water data accessible to everyone, so we welcome contributions of all kinds -- code, documentation, bug reports, and ideas.

---

## Getting Started

### Prerequisites

- **Python 3.10+**
- **Git**
- A free [NASA Earthdata account](https://urs.earthdata.nasa.gov/users/new) (optional -- the pipeline works without it using synthetic data)

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/Promeos/fresh-water.git
cd fresh-water

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Create a .env file for NASA credentials
echo 'EARTHDATA_USERNAME=your_username' >> .env
echo 'NASA_API_KEY=your_key' >> .env

# 5. Run the pipeline to generate dashboard data
python -m pipeline.export

# 6. View the dashboard locally
python -m http.server 8000 --directory docs
# Open http://localhost:8000 in your browser
```

### Running Tests

```bash
python -m pytest tests/ -v
```

---

## Project Structure

```
fresh-water/
  pipeline/               # Python data pipeline
    config.py             # Shared settings (region, URLs, time range)
    fetch_grace.py        # GRACE-FO satellite water storage data
    fetch_gpm.py          # GPM precipitation data
    fetch_population.py   # Census population grid
    process.py            # Statistical analysis and impact metrics
    export.py             # Exports JSON for the frontend
  docs/                   # GitHub Pages static site
    index.html            # Dashboard page
    css/style.css         # Styles (dark theme, CSS custom properties)
    js/dashboard.js       # Chart rendering with Plotly.js
    data/                 # Pipeline JSON output (do not edit by hand)
```

---

## How to Contribute

### Reporting Bugs

Open an issue and include:
- What you expected to happen
- What actually happened
- Steps to reproduce
- Your Python version and OS

### Suggesting Features

Open an issue with the label `enhancement`. Describe:
- The problem you want to solve
- Your proposed solution
- Who benefits from this change

### Submitting Code Changes

1. **Fork** the repository and create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Make your changes** following the code style guidelines below.
3. **Test** your changes:
   ```bash
   python -m pytest tests/ -v
   python -m pipeline.export   # Make sure the pipeline still runs
   ```
4. **Commit** with a clear message:
   ```bash
   git commit -m "Add: brief description of what and why"
   ```
5. **Push** and open a Pull Request against `main`.

### PR Guidelines

- Keep PRs focused -- one feature or fix per PR
- Include a description of what changed and why
- If you change pipeline output, regenerate the JSON files and include them
- Add or update tests for new pipeline logic
- Update documentation if you change how metrics are calculated

---

## Code Style

### Python (pipeline/)

- **Docstrings:** Every module, class, and public function needs a docstring
- **Logging:** Use `logging` (never `print()`) for output
- **Paths:** Use `pathlib.Path` for all file paths
- **Config:** Import shared constants from `pipeline.config` -- do not hardcode region bounds, URLs, or thresholds
- **Reproducibility:** Use fixed `np.random.seed()` values in any synthetic data generation
- **JSON export:** Use compact formatting: `json.dump(data, f, separators=(",", ":"))`
- **Rounding:** Round exported values to 1--3 decimal places to keep file sizes reasonable

### JavaScript (docs/js/)

- **Vanilla JS only** -- no frameworks or build tools
- **Plotly.js** for all charts (loaded via CDN)
- Use the shared `BASE_LAYOUT` and `PLOTLY_CONFIG` constants for chart consistency

### CSS (docs/css/)

- Use CSS custom properties defined in `:root` for colors and spacing
- Dark theme by default
- Cards use `border-radius: 12px` and `border: 1px solid var(--border)`
- Responsive breakpoint at `768px`

---

## Key Concepts for New Contributors

If you are new to the science behind this project, here are some terms you will encounter:

| Term | Meaning |
|------|---------|
| **TWS** | Terrestrial Water Storage -- total water on and below the land surface |
| **GRACE-FO** | Twin satellites that measure gravity changes caused by shifting water mass |
| **Mascon** | "Mass concentration" -- a tile on Earth's surface used to estimate local gravity/water changes |
| **IMERG** | Algorithm that merges data from multiple rain-measuring satellites into one precipitation estimate |
| **Anomaly** | Difference from a reference average (here, the 2004--2009 baseline) |
| **LWE** | Liquid Water Equivalent -- expressing water volume as a uniform layer thickness in centimeters |

---

## Questions?

Open an issue or reach out on [GitHub](https://github.com/Promeos).
