#!/usr/bin/env python3
"""Export the Python contracts (single source of truth) for the TypeScript side.

Writes into packages/contracts/:
  schema/corvo.schema.json        JSON Schema bundle ($defs for every exported model)
  schema/provenance-labels.json   UI label per DataKind
  src/types.gen.ts                TypeScript types generated from the schema
  fixtures/*.mock.json            the MOCK region packs
  fixtures/provenance_cases.json  Provenance cases + Python's verdict (cross-language drift test)

Run:  python tools/export_contracts.py          (writes)
      python tools/export_contracts.py --check  (exit 1 if committed files are stale)
"""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))
sys.path.insert(0, str(ROOT / "tools"))

from pydantic import ValidationError  # noqa: E402
from pydantic.json_schema import models_json_schema  # noqa: E402

from corvo_api.contracts import EXPORTED_MODELS, KIND_LABELS, DataKind, Provenance  # noqa: E402
from corvo_api.mock_packs import CONFIGS, build_mock_pack  # noqa: E402
from gen_ts_types import generate  # noqa: E402

OUT = ROOT / "packages" / "contracts"


def dumps(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def provenance_cases() -> list[dict]:
    now = datetime(2026, 10, 28, tzinfo=UTC).isoformat()
    base = dict(source="Some source", dataset_id=None, version=None, retrieved_at=None,
                resolution_m=None, temporal_resolution=None, license=None, generator=None,
                derived_from=[], notes=None)

    def case(name: str, **kw) -> dict:
        raw = {**base, **kw}
        try:
            Provenance.model_validate(raw)
            valid = True
        except ValidationError:
            valid = False
        return {"name": name, "provenance": raw, "valid": valid}

    cases = [
        case("observed with dataset", kind="observed", dataset_id="HLSS30", retrieved_at=now),
        case("observed without dataset", kind="observed"),
        case("reanalysis without retrieval time", kind="reanalysis", dataset_id="POWER"),
        case("forecast with generator", kind="forecast", dataset_id="X", retrieved_at=now, generator="g"),
        case("mock proper", kind="mock", generator="tests"),
        case("mock without generator", kind="mock"),
        case("mock posing as dataset", kind="mock", generator="g", dataset_id="POWER_DAILY"),
        case("mock with retrieval time", kind="mock", generator="g", retrieved_at=now),
        case("simulated without generator", kind="simulated"),
        case("simulated proper", kind="simulated", generator="aquacrop"),
        case("game assumption proper", kind="game_assumption", generator="corvo-team"),
        case("model estimate proper", kind="model_estimate", dataset_id="SoilGrids", retrieved_at=now),
    ]
    assert any(c["valid"] for c in cases) and any(not c["valid"] for c in cases)
    return cases


def build_outputs() -> dict[Path, str]:
    _, schema = models_json_schema(
        [(m, "serialization") for m in EXPORTED_MODELS], title="CORVO contracts"
    )
    # Every exported model must exist as a named definition (TS generator relies on it).
    for m in EXPORTED_MODELS:
        assert m.__name__ in schema["$defs"], m.__name__
    assert set(KIND_LABELS) == {k.value for k in DataKind}

    files: dict[Path, str] = {
        OUT / "schema" / "corvo.schema.json": dumps(schema),
        OUT / "schema" / "provenance-labels.json": dumps(dict(KIND_LABELS)),
        OUT / "src" / "types.gen.ts": generate(schema),
        OUT / "fixtures" / "provenance_cases.json": dumps(provenance_cases()),
    }
    for rid, cfg in CONFIGS.items():
        pack = build_mock_pack(cfg)
        files[OUT / "fixtures" / f"{rid}.mock.json"] = dumps(pack.model_dump(mode="json"))
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    files = build_outputs()
    stale = [p for p, text in files.items() if not p.exists() or p.read_text(encoding="utf-8") != text]
    if args.check:
        for p in stale:
            print(f"STALE: {p.relative_to(ROOT)}")
        print("contracts up to date" if not stale else "run: python tools/export_contracts.py")
        return 1 if stale else 0
    for p, text in files.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        print(f"wrote {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
