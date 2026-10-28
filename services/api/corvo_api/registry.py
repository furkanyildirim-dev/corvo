"""Framework-agnostic region lookup. Real packs (data/regions/<id>.json) win over mocks."""

import json
import os
from pathlib import Path

from pydantic import BaseModel

from .contracts import RegionPack, data_status
from .contracts.provenance import DataStatus
from .mock_packs import CONFIGS, build_mock_pack

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "regions"


class RegionSummary(BaseModel):
    id: str
    name: str
    center: tuple[float, float]
    data_status: DataStatus


def data_dir() -> Path:
    return Path(os.environ.get("CORVO_REGION_DIR", DEFAULT_DATA_DIR))


def region_ids(directory: Path | None = None) -> list[str]:
    directory = directory or data_dir()
    real = {p.stem for p in directory.glob("*.json")} if directory.is_dir() else set()
    return sorted(real | set(CONFIGS))


def load_pack(region_id: str, directory: Path | None = None) -> RegionPack:
    """Load a validated pack. Raises KeyError for unknown ids."""
    directory = directory or data_dir()
    path = directory / f"{region_id}.json"
    if path.is_file():
        return RegionPack.model_validate(json.loads(path.read_text(encoding="utf-8")))
    if region_id in CONFIGS:
        return build_mock_pack(CONFIGS[region_id])
    raise KeyError(region_id)


def summaries(directory: Path | None = None) -> list[RegionSummary]:
    out = []
    for rid in region_ids(directory):
        pack = load_pack(rid, directory)
        out.append(
            RegionSummary(
                id=pack.id, name=pack.name, center=pack.site.center, data_status=data_status(pack)
            )
        )
    return out
