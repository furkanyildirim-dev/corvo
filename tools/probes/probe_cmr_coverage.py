#!/usr/bin/env python3
"""PROBE: which NASA collections cover each pilot AOI? (NASA CMR search API, stdlib only)

Run:  python tools/probes/probe_cmr_coverage.py [--start 2024-01-01 --end 2024-12-31]
No Earthdata login is needed for CMR *search*. Downloading granules later needs a token
(never commit it; see docs/SOURCES.md).

We do NOT hard-code collection short names for NISAR: we search by keyword and print what CMR
actually reports, then count granules over each AOI. Verify the printed IDs before relying on them.
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request

CMR = "https://cmr.earthdata.nasa.gov/search"
AOIS = {  # west, south, east, north (approximate, mirrors the MOCK pack bboxes)
    "cukurova": (35.23, 36.83, 35.47, 37.07),
    "konya": (32.70, 37.40, 33.00, 37.70),
}
# (label, search keyword for collections)
TARGETS = [
    ("HLS Sentinel-2 (HLSS30)", "HLSS30"),
    ("HLS Landsat (HLSL30)", "HLSL30"),
    ("MODIS Terra vegetation indices 250 m", "MOD13Q1"),
    ("VIIRS vegetation indices", "VNP13"),
    ("NISAR GCOV", "NISAR GCOV"),
    ("NISAR soil moisture", "NISAR soil moisture"),
]


def get(path: str, **params) -> dict:
    url = f"{CMR}/{path}?{urllib.parse.urlencode(params, doseq=True)}"
    with urllib.request.urlopen(url, timeout=60) as r:  # noqa: S310
        return json.load(r)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2024-01-01")
    ap.add_argument("--end", default="2024-12-31")
    args = ap.parse_args()
    for label, kw in TARGETS:
        try:
            cols = get("collections.json", keyword=kw, page_size=5)["feed"]["entry"]
        except Exception as e:  # noqa: BLE001
            print(f"[FAIL] {label}: {type(e).__name__}: {e}")
            continue
        if not cols:
            print(f"[NONE] {label}: no collection matches keyword {kw!r}")
            continue
        for col in cols[:3]:
            cid, title = col["id"], col["title"]
            print(f"\n{label}\n  collection {cid} | {title} | v{col.get('version_id')}")
            for aoi, (w, s, e, n) in AOIS.items():
                hits = get(
                    "granules.json", collection_concept_id=cid, bounding_box=f"{w},{s},{e},{n}",
                    temporal=f"{args.start}T00:00:00Z,{args.end}T23:59:59Z", page_size=1,
                )
                print(f"    {aoi}: granule hits in window = {hits['feed'].get('hits', 'n/a')}"
                      if "feed" in hits else f"    {aoi}: unexpected response")
    return 0


if __name__ == "__main__":
    sys.exit(main())
