"""SimState: the full trajectory produced by a simulation engine for one plan + scenario."""

from datetime import date
from typing import Literal

from pydantic import Field, model_validator

from .management import ManagementPlan
from .provenance import ContractModel, DataBlock, DataKind
from .region import Id
from .scenario import ClimateScenario

CropStage = Literal[
    "fallow", "emergence", "vegetative", "reproductive", "senescence", "harvested", "failed"
]


class EngineInfo(ContractModel):
    name: str
    version: str
    is_mock: bool


class ParcelDayState(ContractModel):
    """Per-parcel daily state. All water quantities are MODEL outputs (root-zone bucket)."""


    parcel_id: str
    crop_id: str | None
    stage: CropStage
    root_zone_water_mm: float = Field(ge=0)
    taw_mm: float = Field(ge=0, description="Total available water in the root zone")
    depletion_mm: float = Field(ge=0)
    water_stress_ks: float = Field(ge=0, le=1, description="1 = no stress")
    canopy_cover: float = Field(ge=0, le=1)
    biomass_t_ha: float = Field(ge=0)
    rain_mm: float = Field(ge=0)
    irrigation_mm: float = Field(ge=0)
    et_actual_mm: float = Field(ge=0)


class SimDay(ContractModel):
    day: int = Field(ge=0)
    date: date
    parcels: list[ParcelDayState]


class SeasonSummary(ContractModel):
    season: int = Field(ge=1)
    parcel_id: str
    crop_id: str | None
    irrigation_total_mm: float = Field(ge=0)
    et_total_mm: float = Field(ge=0)
    relative_yield_index: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Model-relative yield (0-1). NOT a measured or forecast yield in t/ha.",
    )


class SimState(DataBlock):
    run_id: str = Id
    region_id: str = Id
    plan_id: str = Id
    scenario_id: str = Id
    engine: EngineInfo
    days: list[SimDay]
    summaries: list[SeasonSummary]

    @model_validator(mode="after")
    def _engine_matches_provenance(self) -> "SimState":
        """A mock engine can only ever produce MOCK output; a real one produces SIMULATED."""
        want = DataKind.MOCK if self.engine.is_mock else DataKind.SIMULATED
        if self.provenance.kind != want:
            raise ValueError(
                f"engine.is_mock={self.engine.is_mock} requires provenance.kind={want.value}"
            )
        return self


class SimRequest(ContractModel):
    """API envelope: no numeric data of its own."""


    plan: ManagementPlan
    scenario: ClimateScenario
