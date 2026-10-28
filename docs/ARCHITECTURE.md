# Architecture (M0)

```
Python contracts (pydantic)  ──tools/export_contracts.py──►  JSON Schema + TS types + fixtures
        │ single source of truth                                   │
        ▼                                                          ▼
services/api (FastAPI)  ◄── HTTP ──►  apps/web (React shell · MapLibre world · Phaser farm)
  registry → RegionPack                  validates every payload (schema + provenance guard)
  /simulate (501 until M4)               renders; never computes science
```

## Why this shape

- **One source of truth.** Contracts are written once (Python). TS types, JSON Schema and fixtures are generated; a test fails if they go stale.
- **Regions are data.** `RegionPack` + crop catalog + resource rules + scenarios. Both pilots are built by the same function (`mock_packs.build_mock_pack`); a real pack is just `data/regions/<id>.json` that overrides the mock. M6 acceptance: Konya runs with zero engine changes.
- **Provenance is structural.** Every data block extends `DataBlock` (mandatory `provenance`). Rules in `contracts/provenance.py`:
  real kinds must cite dataset + time; mock may not cite a dataset; mock taint survives derivation; a mock engine can only emit mock output; scenarios never mutate baselines and clear stale ET0.
  The client re-checks the same rules, and a cross-language test prevents drift.
- **Separation of duties.** React = shell/UI state. MapLibre = world map. Phaser = farm rendering (reads `SimState`, computes nothing). Python = data + science.
- **Logical grid ≠ render grid.** Data geometry stays in lon/lat (+ `local_epsg`); art style (open decision D11) only affects rendering.

## Contract map

`Provenance` · `RegionPack` (site, parcels, soils, climate, crops, rules, observation layers) · `ManagementPlan` ·
`ClimateScenario` (+ `apply_scenario`) · `SimState` (days, summaries, engine info) · `SimRequest`.

## Deferred (by design)

Simulation engine (M4 mock → M7 AquaCrop), real data pipeline (M3/M7), globe + imagery (M1), art (D11), Fork the Future (M5).
