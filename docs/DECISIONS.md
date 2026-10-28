# CORVO — Decision Log

Newest decisions at the bottom of each section. Status: **Final**, **Open**, **Superseded**.

## Product / design

| # | Decision | Status |
|---|---|---|
| D1 | Mechanical core: Atlas-Diorama-style playable farm + Strata (root-zone cross-section) + Fork the Future | Final |
| D2 | The main experience is a game, not a dashboard | Final |
| D3 | Pilot A: Çukurova / Lower Seyhan (first fully playable region) | Final |
| D4 | Pilot B: Konya Closed Basin (second region, same engine) | Final |
| D5 | One geodata / game / simulation engine; regions differ only in RegionPack, crop catalog, resource rules and scenarios | Final |
| D11 | **Visual style** (isometric pixel-art / original stylised 2.5D / Atlas Diorama) | **Open** — decided after the M1 style trial; not before team sign-off |

## Data integrity

| # | Decision | Status |
|---|---|---|
| D6 | Observed / forecast / simulated are separate states; every data block carries `Provenance` | Final (enforced in code) |
| D7 | NDVI is an observation of vegetation greenness; it is never presented as soil moisture or yield | Final |
| D8 | NISAR/SAR stays "unverified" per region until coverage is confirmed by a probe | Final |
| D10 | Placeholder data is allowed but must be `mock`; mock cannot cite a dataset; mock taint propagates through derivations | Final (enforced in code + tests) |
| D13 | NASA POWER = reanalysis (model-derived); SoilGrids = model estimate; water quotas / pumping costs = game assumptions. None is called "measured" | Final |

## Process

| # | Decision | Status |
|---|---|---|
| D9 | Development starts before the hackathon. The team spoke with the Space Apps ambassador (verbal OK). **Written confirmation still to be recorded** in `PREDEV_APPROVAL.md` | Final, evidence pending |
| D12 | Milestone order revised (below): real NDVI / Raven Vision (M3) and first A/B Fork the Future with MOCK sim (M5) move earlier; science integration (M7) comes last but its risks are probed in M0–M1 | Final |

### Milestone order (supersedes the Phase B plan order)

M0 infrastructure + contracts → M1 style trials + real world map → M2 Çukurova farm, gameplay, raven, basic NPC →
M3 real NDVI layer + Raven Vision → M4 sow / irrigate / harvest, environment parameters, Strata →
M5 first playable Fork the Future (A/B, MOCK sim) → M6 Konya on the same engine → M7 full scientific integration + validation.

Parallel in M0–M1: NASA data access probe, pilot AOI/coordinate verification, AquaCrop feasibility (see `PROBES.md`).

## Superseded assumptions (from the Phase A report)

1. Konya as the single pilot → now Çukurova first, Konya second.
2. Game tile locked to the 10 m data pixel → logical data grid and visual render grid are separate.
3. MODIS NDVI as the long-run live source → MODIS stops science collection in 2027 (Terra Feb, Aqua Sep); keep it as archive/climatology, plan VIIRS/HLS for current seasons.
4. Gouache style implied by the concept name → style is open (D11).

## Challenge status (as of 2026-10-28)

The official Field Shift page blocks automated access, so the full challenge statement could **not** be read.
Third-party sources only confirm that full statements were scheduled for 28 Oct 2026 and that the hackathon runs 14–15 Nov.
No mandatory requirement has been verified. **Action:** team to paste the official statement; then compare against this log.
