#!/usr/bin/env python3
"""PROBE: can we pull NASA POWER daily data for both pilot centres? (stdlib only)

Run:  python tools/probes/probe_nasa_power.py
Needs outbound HTTPS to power.larc.nasa.gov (no key required).
Checks: HTTP 200, expected parameters present, no -999 fill values, 366 days for 2024.
"""

import json
import sys
import urllib.parse
import urllib.request

CENTRES = {"cukurova": (35.35, 36.95), "konya": (32.85, 37.55)}  # lon, lat (approximate)
PARAMS = "T2M_MAX,T2M_MIN,PRECTOTCORR,ALLSKY_SFC_SW_DWN,RH2M,WS2M"
BASE = "https://power.larc.nasa.gov/api/temporal/daily/point"


def fetch(lon: float, lat: float, start: str, end: str) -> dict:
    q = urllib.parse.urlencode(
        dict(parameters=PARAMS, community="AG", longitude=lon, latitude=lat,
             start=start, end=end, format="JSON")
    )
    with urllib.request.urlopen(f"{BASE}?{q}", timeout=60) as r:  # noqa: S310
        return json.load(r)


def main() -> int:
    ok = True
    for name, (lon, lat) in CENTRES.items():
        try:
            data = fetch(lon, lat, "20240101", "20241231")
        except Exception as e:  # noqa: BLE001
            print(f"[FAIL] {name}: {type(e).__name__}: {e}")
            ok = False
            continue
        par = data["properties"]["parameter"]
        missing = [p for p in PARAMS.split(",") if p not in par]
        n = len(par.get("T2M_MAX", {}))
        fills = sum(1 for p in par.values() for v in p.values() if v == -999)
        status = "OK" if not missing and n == 366 and fills == 0 else "CHECK"
        print(f"[{status}] {name}: days={n} missing={missing} fill_values={fills} "
              f"grid_elev={data['geometry']['coordinates'][2]} m")
        ok &= status == "OK"
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
