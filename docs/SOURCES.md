# Sources and licences

## Data products (planned use; provenance kind in brackets)

| Product | Kind | Notes |
|---|---|---|
| NASA POWER daily | reanalysis | Model-derived grid, not station data |
| GPM IMERG | observed (satellite+gauge merged estimate) | Early/Late/Final latencies differ |
| HLS (Sentinel-2 / Landsat) NDVI | observed (index derived from reflectance) | Cloud-limited; 30 m |
| MODIS MOD13Q1 NDVI | observed | Archive/climatology only; MODIS science collection ends 2027 |
| VIIRS vegetation indices | observed | MODIS successor |
| NISAR L-band / ISRO S-band | observed | Calibrated provisional products released July 2026; AOI coverage **not verified** |
| SoilGrids | model_estimate | Not measured on the field |
| ESA WorldCover | observed (classified) | 2020/2021 snapshots |
| FAO-56 / AquaCrop | simulated (method) | Parameters currently MOCK placeholders |

Access tokens (Earthdata, etc.) are never committed (`.gitignore`); raw downloads stay in `data/raw/`.

## Documents consulted for M0 (2026-10-28)

- NASA, "NASA Announces 2025 International Space Apps Challenge Global Winners" (read in full).
- NASA Space Apps 2026 dates (registration page; participant FAQ): statements 28 Oct, event 14–15 Nov.
- ASF NISAR data availability pages; ISRO NISAR S-band release page; NASA ARSET NISAR session 2.
- LAADS DAAC "MODIS to VIIRS transition"; Earthdata alert "Transition from MODIS to VIIRS".
- **Not read:** the official Field Shift 2026 challenge page (automated access blocked).

## Open-source dependencies (declared; install not verified in the M0 sandbox)

| Package | Licence |
|---|---|
| pydantic, FastAPI, uvicorn | MIT / MIT / BSD-3 |
| React, Vite, Phaser | MIT |
| MapLibre GL JS | BSD-3-Clause |
| ajv | MIT |
| AquaCrop-OSPy (M7) | MIT (verify on install) |
