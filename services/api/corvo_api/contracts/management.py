"""ManagementPlan: the player's decisions (crops, sowing, irrigation, nitrogen) per season."""

from typing import Literal

from pydantic import Field, model_validator

from .provenance import ContractModel, DataBlock
from .region import Id, RegionPack


class IrrigationPolicy(ContractModel):
    strategy: Literal["rainfed", "fixed_depth", "deficit_threshold"]
    depth_mm: float | None = Field(default=None, gt=0)
    interval_days: int | None = Field(default=None, ge=1, le=60)
    trigger_depletion_frac: float | None = Field(default=None, gt=0, le=1)
    season_cap_mm: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _by_strategy(self) -> "IrrigationPolicy":
        if self.strategy == "fixed_depth" and (self.depth_mm is None or self.interval_days is None):
            raise ValueError("fixed_depth requires depth_mm and interval_days")
        if self.strategy == "deficit_threshold" and (
            self.depth_mm is None or self.trigger_depletion_frac is None
        ):
            raise ValueError("deficit_threshold requires depth_mm and trigger_depletion_frac")
        return self


class ParcelSeasonPlan(ContractModel):
    parcel_id: str
    crop_id: str | None = Field(default=None, description="None = fallow")
    sowing_doy: int | None = Field(default=None, ge=1, le=366)
    irrigation: IrrigationPolicy
    nitrogen_kg_ha: float = Field(default=0, ge=0, le=400)

    @model_validator(mode="after")
    def _fallow(self) -> "ParcelSeasonPlan":
        if self.crop_id is not None and self.sowing_doy is None:
            raise ValueError("a sown crop needs sowing_doy")
        return self


class SeasonPlan(ContractModel):
    season: int = Field(ge=1)
    parcels: list[ParcelSeasonPlan] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique_parcels(self) -> "SeasonPlan":
        ids = [p.parcel_id for p in self.parcels]
        if len(ids) != len(set(ids)):
            raise ValueError("a parcel may appear only once per season")
        return self


class ManagementPlan(DataBlock):
    """Provenance of a plan is GAME_ASSUMPTION (player decision), never observation."""

    id: str = Id
    region_id: str = Id
    label: str = Field(min_length=1, max_length=24, description="e.g. 'A' or 'B'")
    seasons: list[SeasonPlan] = Field(min_length=1)

    @model_validator(mode="after")
    def _consecutive(self) -> "ManagementPlan":
        nums = [s.season for s in self.seasons]
        if nums != list(range(1, len(nums) + 1)):
            raise ValueError("seasons must be numbered 1..N in order")
        return self


def validate_plan_against_region(plan: ManagementPlan, pack: RegionPack) -> list[str]:
    """Cross-reference check. Returns a list of human-readable problems (empty = OK)."""
    problems: list[str] = []
    if plan.region_id != pack.id:
        problems.append(f"plan is for region {plan.region_id!r}, pack is {pack.id!r}")
    parcel_ids = {p.id for p in pack.parcels.parcels}
    crop_ids = {c.id for c in pack.crops.crops}
    for season in plan.seasons:
        for pp in season.parcels:
            if pp.parcel_id not in parcel_ids:
                problems.append(f"season {season.season}: unknown parcel {pp.parcel_id!r}")
            if pp.crop_id is not None and pp.crop_id not in crop_ids:
                problems.append(f"season {season.season}: crop {pp.crop_id!r} not in catalog")
    return problems
