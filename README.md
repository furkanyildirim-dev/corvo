# CORVO — Real Earth. Playable Digital Twins. Different Futures.

A farming strategy game built on real-world coordinates. Pilot regions: Çukurova / Lower Seyhan and Konya Closed Basin.

> **Status: M0 (foundation).** There is no playable game yet. All region data is **MOCK** and labelled as such.
> See `docs/STATUS.md` for exactly what has been run and what has not.

## Layout

```
apps/web/            React + TS shell, MapLibre world map, Phaser farm scene
packages/contracts/  generated TS types, JSON Schema, provenance guard, fixtures
services/api/        FastAPI + pydantic contracts (source of truth), mock region packs, tests
tools/               contract export, TS generator, technical probes
data/regions/        real RegionPacks (override mocks); data/raw/ is git-ignored
docs/                DECISIONS, ARCHITECTURE, SOURCES, AI_LOG, PROBES, STATUS, PREDEV_APPROVAL
```

## Run (needs network for installs)

```bash
# API
python3 -m venv services/api/.venv && source services/api/.venv/bin/activate
pip install -e "services/api[dev]"
cd services/api && python -m pytest -q && uvicorn corvo_api.main:app --reload --port 8000

# Web (second terminal, repo root)
npm install
npm test            # api + contracts + web tests
npm run dev:web     # http://localhost:5173
```

After editing any Python contract: `npm run gen` (regenerates schema, TS types, fixtures).
`npm run gen:check` fails if they are stale; pytest runs the same check.

## Ground rules

- Real, reanalysis, estimated, assumed, simulated and mock data are different things; every data block says which (`Provenance`).
- Observed Earth is never modified by a scenario; scenarios produce a new simulated series.
- Do not commit credentials (Earthdata tokens). Document AI-assisted work in `docs/AI_LOG.md`.
