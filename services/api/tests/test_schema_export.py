"""The exported JSON Schema (what TypeScript/ajv consumes) must accept what Python produces."""

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from corvo_api.contracts import EXPORTED_MODELS
from corvo_api.mock_packs import CONFIGS, build_mock_pack

ROOT = Path(__file__).resolve().parents[3]
SCHEMA = json.loads((ROOT / "packages/contracts/schema/corvo.schema.json").read_text("utf-8"))


def validator(defn: str) -> Draft202012Validator:
    return Draft202012Validator({"$ref": f"#/$defs/{defn}", "$defs": SCHEMA["$defs"]})


@pytest.mark.parametrize("rid", sorted(CONFIGS))
def test_python_output_validates_against_exported_schema(rid):
    raw = build_mock_pack(CONFIGS[rid]).model_dump(mode="json")
    errors = list(validator("RegionPack").iter_errors(raw))
    assert errors == [], errors[:3]


def test_schema_has_every_exported_model():
    assert {m.__name__ for m in EXPORTED_MODELS} <= set(SCHEMA["$defs"])


def test_schema_is_strict():
    raw = build_mock_pack(CONFIGS["konya"]).model_dump(mode="json")
    v = validator("RegionPack")
    missing = copy.deepcopy(raw)
    del missing["climate"]["provenance"]
    assert not v.is_valid(missing)
    extra = copy.deepcopy(raw)
    extra["surprise"] = 1
    assert not v.is_valid(extra)
    wrong = copy.deepcopy(raw)
    wrong["site"]["center"] = ["35", "37"]
    assert not v.is_valid(wrong)


def test_committed_contract_files_are_not_stale():
    """Fails if someone edits a contract but forgets `python tools/export_contracts.py`."""
    res = subprocess.run(
        [sys.executable, str(ROOT / "tools/export_contracts.py"), "--check"],
        capture_output=True, text=True,
    )
    assert res.returncode == 0, res.stdout + res.stderr
