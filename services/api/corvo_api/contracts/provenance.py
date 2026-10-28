"""Provenance: every data-bearing block must say what it is and where it came from.

Design rules (enforced in code, covered by tests):

1. Real kinds (observed / reanalysis / forecast / model_estimate) MUST cite a dataset and a
   retrieval time. They can never be produced by a generator.
2. MOCK data MUST NOT cite a real dataset or retrieval time, and MUST name its generator.
   This prevents placeholder numbers from passing as a real NASA product.
3. Anything derived from a MOCK parent stays MOCK ("taint propagation"), see ``derive``.
4. Derived values are never "observed": ``derive`` refuses real kinds.
"""

from collections.abc import Iterator, Sequence
from enum import StrEnum
from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class DataKind(StrEnum):
    OBSERVED = "observed"  # direct satellite / in-situ observation (or an index derived from one)
    REANALYSIS = "reanalysis"  # gridded model-derived product (e.g. NASA POWER)
    FORECAST = "forecast"  # numerical weather prediction
    MODEL_ESTIMATE = "model_estimate"  # ML / pedotransfer estimate (e.g. SoilGrids)
    GAME_ASSUMPTION = "game_assumption"  # human-chosen game parameter, not measured
    SIMULATED = "simulated"  # output of a scientific model under a scenario
    MOCK = "mock"  # placeholder; NOT real data of any kind


# Single source of truth for UI labels. Exported to JSON for the web client.
KIND_LABELS: dict[str, str] = {
    DataKind.OBSERVED: "OBSERVED",
    DataKind.REANALYSIS: "REANALYSIS (model-derived)",
    DataKind.FORECAST: "FORECAST",
    DataKind.MODEL_ESTIMATE: "ESTIMATED",
    DataKind.GAME_ASSUMPTION: "GAME ASSUMPTION",
    DataKind.SIMULATED: "SIMULATED",
    DataKind.MOCK: "MOCK",
}

REAL_KINDS = frozenset(
    {DataKind.OBSERVED, DataKind.REANALYSIS, DataKind.FORECAST, DataKind.MODEL_ESTIMATE}
)
GENERATED_KINDS = frozenset({DataKind.MOCK, DataKind.GAME_ASSUMPTION, DataKind.SIMULATED})

DataStatus = Literal["contains_mock", "no_mock"]


class ContractModel(BaseModel):
    """Base for all contract models: strict (no unknown fields), and defaults are emitted.

    ``json_schema_serialization_defaults_required`` makes fields with defaults *required* in
    the exported schema, matching the JSON the API actually returns (no ``?`` in TS types).
    """

    model_config = ConfigDict(extra="forbid", json_schema_serialization_defaults_required=True)


class Provenance(ContractModel):
    model_config = ConfigDict(frozen=True)

    kind: DataKind
    source: str = Field(min_length=3, description="Human-readable origin, e.g. 'NASA POWER'")
    dataset_id: str | None = None
    version: str | None = None
    retrieved_at: AwareDatetime | None = None
    resolution_m: float | None = Field(default=None, gt=0)
    temporal_resolution: str | None = None
    license: str | None = None
    generator: str | None = Field(
        default=None, description="Code path or person that produced generated values"
    )
    derived_from: list[str] = Field(default_factory=list)
    notes: str | None = None

    @model_validator(mode="after")
    def _check_invariants(self) -> "Provenance":
        if self.kind in REAL_KINDS:
            if not self.dataset_id or self.retrieved_at is None:
                raise ValueError(
                    f"{self.kind.value} provenance must cite dataset_id and retrieved_at"
                )
            if self.generator:
                raise ValueError(f"{self.kind.value} data cannot come from a generator")
        if self.kind == DataKind.MOCK and (self.dataset_id or self.retrieved_at is not None):
            raise ValueError("mock provenance must not cite a real dataset or retrieval time")
        if self.kind in GENERATED_KINDS and not self.generator:
            raise ValueError(f"{self.kind.value} provenance must name its generator")
        return self

    @property
    def is_mock(self) -> bool:
        return self.kind == DataKind.MOCK

    @property
    def label(self) -> str:
        return KIND_LABELS[self.kind]


class DataBlock(ContractModel):
    """Base for every block that carries data: provenance is mandatory."""

    provenance: Provenance


def describe(p: Provenance) -> str:
    return f"{p.kind.value}:{p.source}"


def derive(
    kind: DataKind,
    *,
    source: str,
    generator: str,
    parents: Sequence[Provenance],
    notes: str | None = None,
) -> Provenance:
    """Provenance for a value computed from ``parents``.

    A derived value is never an observation, and mock taint propagates: if any parent is
    MOCK the result is MOCK, no matter which kind the caller asked for.
    """
    if kind in REAL_KINDS:
        raise ValueError("derived values can never be labelled as real observations")
    out_kind = DataKind.MOCK if any(p.is_mock for p in parents) else kind
    return Provenance(
        kind=out_kind,
        source=source,
        generator=generator,
        derived_from=[describe(p) for p in parents],
        notes=notes,
    )


def iter_provenance(obj: Any) -> Iterator[Provenance]:
    """Yield every Provenance reachable from ``obj`` (models, lists, tuples, dicts)."""
    if isinstance(obj, Provenance):
        yield obj
    elif isinstance(obj, BaseModel):
        for name in type(obj).model_fields:
            yield from iter_provenance(getattr(obj, name))
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            yield from iter_provenance(item)
    elif isinstance(obj, dict):
        for item in obj.values():
            yield from iter_provenance(item)


def data_status(obj: Any) -> DataStatus:
    return "contains_mock" if any(p.is_mock for p in iter_provenance(obj)) else "no_mock"


def uncovered_numeric_models(obj: Any, covered: bool = False) -> list[str]:
    """Names of model instances that hold numbers but sit outside any DataBlock.

    Guards against someone adding numeric data to a contract without provenance.
    ``Provenance`` itself is exempt (its numbers describe the data, not the data).
    """
    out: list[str] = []
    if isinstance(obj, Provenance):
        return out
    if isinstance(obj, BaseModel):
        now_covered = covered or isinstance(obj, DataBlock)
        has_numbers = any(
            isinstance(v, (int, float)) and not isinstance(v, bool)
            or (isinstance(v, (list, tuple)) and any(isinstance(x, (int, float)) for x in v))
            for v in (getattr(obj, n) for n in type(obj).model_fields)
        )
        if has_numbers and not now_covered:
            out.append(type(obj).__name__)
        for name in type(obj).model_fields:
            out.extend(uncovered_numeric_models(getattr(obj, name), now_covered))
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            out.extend(uncovered_numeric_models(item, covered))
    elif isinstance(obj, dict):
        for item in obj.values():
            out.extend(uncovered_numeric_models(item, covered))
    return out
