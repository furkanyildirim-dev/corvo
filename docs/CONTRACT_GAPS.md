# Contract gaps vs. Field Shift core needs (M0 check)

Basis: the **team brief** (farmer priorities, local soil information, crop properties, multi-season
rotation). The official Field Shift statement was **not** read (the page blocks automated access),
so this is a check against the brief, not against the official text. No re-architecture proposed;
each gap is additive (new optional fields / new models in `corvo_api/contracts`).

| Need | Represented today | Gap | Suggested additive fix | When |
|---|---|---|---|---|
| **Farmer priorities** | Only `ResourceRules.starting_budget` and the plan itself. | **Missing.** No model for goals (e.g. income vs. water saving vs. soil health), risk tolerance, constraints (crops they cannot/will not grow, labour, capital), or weights used to rank A vs B. | New `FarmerPriorities` (weights, hard constraints, risk attitude), referenced by `ManagementPlan`; Fork comparison reads the weights. Weights are `game_assumption` provenance. | M5 (before first A/B) |
| **Local soil information** | `SoilProfile`/`SoilLayer` (theta_wp < fc < sat, ksat) with provenance, per parcel via `SoilSet`. | **Partial.** No organic carbon, texture class, salinity/EC, pH, drainage class, or "farmer-reported vs. SoilGrids estimate" source distinction. Provenance kinds allow `model_estimate`, but there is no `field_measured`/`farmer_reported` kind. | Add optional soil fields; decide whether to add a `farmer_reported` DataKind (changes provenance rules + the TS drift test; do deliberately). | M7 |
| **Crop properties** | `CropSpec`: kc ini/mid/end, stage days, max root depth, depletion fraction p, Ky, Tbase. All current values are MOCK placeholders. | **Partial.** No planting-window / calendar constraints, cultivar/variety, heat/frost thresholds, salinity tolerance, nitrogen response, price/cost per crop, or rotation-relevant traits (legume, family, residue). | Add optional fields; replace placeholder numbers from FAO-56 / AquaCrop data (M7). | M4 (prices/costs), M7 |
| **Multi-season rotation** | `ManagementPlan` has numbered seasons with per-parcel crop and irrigation policy; `validate_plan_against_region` checks it. | **Partial.** (a) No rotation rules (same-family penalty, fallow, legume benefit). (b) No carry-over state between seasons (soil water/organic matter/residue/salinity at season end → next start). (c) Climate is a single-year series; season ↔ calendar-year mapping is undefined. (d) `SeasonSummary` has water/yield-index only; **no soil-health outputs**. | `RotationRule` list on the region/crop catalog; `SeasonCarryover` block in `SimState`; multi-year `ClimateSeries` or explicit year mapping; extra summary indicators only where a model supports them. | M5 (carry-over, calendar), M7 (rules, soil-health) |

## Also noted
- `relative_yield_index` is a 0–1 model indicator, not a yield forecast; keep it labelled so.
- `/simulate` returns 501: there is no simulation engine yet, so none of the above can be exercised end-to-end.
- Climate scenarios cover temperature offset and precipitation scale only (matches the brief).
