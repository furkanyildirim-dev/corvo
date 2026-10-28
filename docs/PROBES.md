# Parallel technical probes (M0–M1)

Scripts live in `tools/probes/`. **None has produced a real result yet** — the M0 build sandbox blocked
the required network hosts. Run them on a networked machine and paste the output into the "Result" cells.

| # | Question | Script | State | Result |
|---|---|---|---|---|
| P1 | Can we pull NASA POWER daily data for both centres? | `probe_nasa_power.py` | **Not run** — `power.larc.nasa.gov` is not on the sandbox allowlist | _paste_ |
| P2 | Which NASA collections (HLS, MODIS/VIIRS NDVI, NISAR) cover each AOI, and how many granules per year? | `probe_cmr_coverage.py` | **Not run** — network | _paste_ |
| P3 | Is AquaCrop-OSPy usable for our crops, and how long does a season take? | `probe_aquacrop.py` | **Not run** — `pip install aquacrop` blocked (pypi.org 403) | _paste_ |
| P4 | Are the approximate pilot centres on real cropland? | _to write_: sample ESA WorldCover (open tiles) at each centre/bbox, then digitise real parcels | Not started | — |

## Decision rules for the results

- **P1 fails or has gaps** → pin a cached POWER extract into the RegionPack and label it `reanalysis` with retrieval date.
- **P2 shows no NISAR coverage for an AOI** → SAR layer stays `unverified` / hidden for that region; consider Sentinel-1 as a documented substitute.
- **P3: crop missing** → drop it from the first catalogue or supply custom parameters validated against literature (never silently reuse another crop's).
- **P3: > ~0.5 s per single-season run** → the in-game preview uses the light water-balance emulator; AquaCrop is used for the Fork the Future "official" run.
- **P4 fails** → move the centre / bbox, re-export packs, keep everything else unchanged.
