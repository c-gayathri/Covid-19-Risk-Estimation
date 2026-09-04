# Covid-19 Risk Estimation

A multi-page Dash web app that estimates personal + city-level Covid-19 risk for Delhi / Chennai.

It combines 4 risk dimensions into an overall score:

- **Risk Profile** (`pages/riskProfile.py`): P(infection by gender/city) × P(adverse outcome by age/diabetes/hypertension), plus household-member risk (SAR = 0.2). Bullet gauge scaled to 15.
- **Health System** (`pages/healthSystem.py`): Hospital bed + ICU occupancy → 4-level lookup → cumulative gauge.
- **Prevalence** (`pages/prevalence.py`): Active cases + growth rate → 4×4 lookup → cumulative gauge.
- **Transmission** (`pages/transmission.py`): Bar chart of transmission risk by place/type per city.
- **Overall** (`pages/overall.py`): Sums the 4 normalized stores (`risk_store`, `health_store`, `prev_store`, `trans_store`) → gauge / 4.

Routing lives in `index.py`; shared Dash instance in `app.py`. Live data comes from a Google Sheet via `gspread`.

## Project structure

```text
app.py          # shared Dash app + Flask server
index.py        # router + entry point (run this)
pages/
  riskProfile.py
  healthSystem.py
  prevalence.py
  transmission.py
  overall.py
requirements.txt  # pinned dependencies (Dash 1.x to match current imports)
cred.json       # Google service-account key (required at runtime, do not commit)
```

## Prerequisites

- Python 3.8 or 3.9 recommended (the pinned `dash==1.20.0` set installs cleanest there; newer Pythons may struggle with the legacy Flask/Jinja pins)
- Google service-account `cred.json` with access to the backing Sheet
- Dependencies are pinned in `requirements.txt`: `dash`, `dash-core-components`, `dash-html-components`, `dash-bootstrap-components`, `pandas`, `numpy`, `plotly`, `gspread`

> The code imports `dash_core_components` and `dash_html_components` (removed in Dash 2+), so `requirements.txt` pins `dash==1.20.0`. To use modern Dash instead, change every `import dash_core_components as dcc` → `from dash import dcc` and `import dash_html_components as html` → `from dash import html`, then install unpinned `dash`.

## How to run

```bash
cd Covid-19-Risk-Estimation

# 1. Create and activate a venv
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add credentials
# Place your Google service-account key as ./cred.json in the repo root
# and share the backing Google Sheet with its client_email.
ls cred.json

# 4. Run the app
python index.py
```

Open:

- <http://127.0.0.1:8050> (defaults to Risk Profile)
- <http://127.0.0.1:8050/pages/riskProfile>
- <http://127.0.0.1:8050/pages/healthSystem>
- <http://127.0.0.1:8050/pages/prevalence>
- <http://127.0.0.1:8050/pages/transmission>
- <http://127.0.0.1:8050/pages/overall>

`index.py` also tries to `pip install` missing packages at startup; prefer installing them beforehand as above.

## Configuration

The Sheet ID is currently hardcoded in each file under `pages/*.py`:

```python
gc = gspread.service_account(filename='cred.json')
sh = gc.open_by_key('1TFvNZqHILzKK7VttupYZgrSNgiZXkGlEicvc50VhGvM')
```

Expected worksheets: `P_inf`, `P_adverse`, `HealthSystem`, `Prevalence`, `Prevalence_Live`, `Transmission`, `Looking up latest` (ID string in `F2`, e.g. `11100` = gender/city/age/diabetes/hypertension codes).

To retarget, change `open_by_key(...)` and keep the same sheet/tab names.
