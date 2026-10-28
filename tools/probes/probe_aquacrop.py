#!/usr/bin/env python3
"""PROBE: is AquaCrop-OSPy usable for CORVO's crops, and fast enough for a game loop?

Run:  pip install aquacrop && python tools/probes/probe_aquacrop.py
Checks:
  1. the package imports and a bundled example run completes (timing reported)
  2. which of our wanted crops ship as built-in crop parameter files
Anything not built in must be supplied as custom crop parameters (and validated) or dropped.
"""

import importlib.util
import sys
import time
from pathlib import Path

WANTED = ["wheat", "barley", "maize", "cotton", "soybean", "sugar_beet", "chickpea"]


def builtin_crops() -> set[str]:
    spec = importlib.util.find_spec("aquacrop")
    if spec is None or spec.submodule_search_locations is None:
        raise RuntimeError("aquacrop is not installed")
    root = Path(next(iter(spec.submodule_search_locations)))
    names = {p.stem.lower() for p in root.rglob("*.txt") if "crop" in str(p).lower()}
    names |= {p.stem.lower() for p in root.rglob("*.py") if "crop" in str(p).lower()}
    return names


def main() -> int:
    try:
        from aquacrop import AquaCropModel, Crop, InitialWaterContent, Soil
        from aquacrop.utils import get_filepath, prepare_weather
    except Exception as e:  # noqa: BLE001
        print(f"[FAIL] import: {type(e).__name__}: {e}")
        return 1

    names = builtin_crops()
    print("candidate built-in crop files/modules found:", sorted(n for n in names if n.isalpha())[:40])
    for crop in WANTED:
        key = crop.replace("_", "")
        hit = any(key in n.replace("_", "") for n in names)
        print(f"  {crop:<11} {'found in package files' if hit else 'NOT FOUND (custom params needed)'}")

    wdf = prepare_weather(get_filepath("tunis_climate.txt"))
    t0 = time.perf_counter()
    model = AquaCropModel(
        "1979/10/01", "1985/05/30", wdf, Soil("SandyLoam"),
        Crop("Wheat", planting_date="10/01"), InitialWaterContent(value=["FC"]),
    )
    model.run_model(till_termination=True)
    dt = time.perf_counter() - t0
    res = model.get_simulation_results()
    print(f"[OK] example run: {len(res)} seasons in {dt:.2f}s ({dt / max(len(res), 1):.3f}s/season)")
    print(res.head(2).to_string())
    print("\nGAME-LOOP BUDGET: target < 2 s per played season incl. A/B ensemble -> see FORK notes in docs/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
