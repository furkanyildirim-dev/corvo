"""RegionPack: everything the engine needs to run one region. Regions differ only here."""

from datetime import date
from typing import Literal

from pydantic import Field, model_validator

from .provenance import ContractModel, DataBlock

LonLat = tuple[float, float]  # (longitude, latitude), WGS84 degrees
Id = Field(pattern=r"^[a-z0-9_-]+$", min_length=1, max_length=48)


class SiteGeometry(DataBlock):
    bbox: tuple[float, float, float, float] = Field(description="west, south, east, north")
    center: LonLat
    local_epsg: int = Field(description="Projected CRS used to align the game grid (e.g. UTM)")

    @model_validator(mode="after")
    def _check(self) -> "SiteGeometry":
        w, s, e, n = self.bbox
        if not (-180 <= w < e <= 180 and -90 <= s < n <= 90):
            raise ValueError("bbox must be (west < east, south < north) within WGS84 limits")
        lon, lat = self.center
        if not (w <= lon <= e and s <= lat <= n):
            raise ValueError("center must lie inside bbox")
        return self


class Parcel(ContractModel):
    id: str = Id
    name: str
    ring: list[LonLat] = Field(min_length=4, description="Closed ring, lon/lat")
    area_ha: float = Field(gt=0)
    soil_id: str

    @model_validator(mode="after")
    def _closed(self) -> "Parcel":
        if self.ring[0] != self.ring[-1]:
            raise ValueError(f"parcel {self.id}: ring must be closed")
        return self


class ParcelSet(DataBlock):
    parcels: list[Parcel] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique(self) -> "ParcelSet":
        ids = [p.id for p in self.parcels]
        if len(ids) != len(set(ids)):
            raise ValueError("parcel ids must be unique")
        return self


class SoilLayer(ContractModel):
    top_cm: float = Field(ge=0)
    bottom_cm: float = Field(gt=0)
    theta_wp: float = Field(gt=0, lt=1, description="Wilting point, m3/m3")
    theta_fc: float = Field(gt=0, lt=1, description="Field capacity, m3/m3")
    theta_sat: float = Field(gt=0, lt=1, description="Saturation, m3/m3")
    ksat_mm_day: float = Field(gt=0)

    @model_validator(mode="after")
    def _ordered(self) -> "SoilLayer":
        if not self.top_cm < self.bottom_cm:
            raise ValueError("layer top must be above bottom")
        if not self.theta_wp < self.theta_fc < self.theta_sat:
            raise ValueError("require theta_wp < theta_fc < theta_sat")
        return self


class SoilProfile(ContractModel):
    id: str = Id
    name: str
    layers: list[SoilLayer] = Field(min_length=1)

    @model_validator(mode="after")
    def _contiguous(self) -> "SoilProfile":
        prev = 0.0
        for layer in self.layers:
            if layer.top_cm != prev:
                raise ValueError(f"soil {self.id}: layers must be contiguous from 0 cm")
            prev = layer.bottom_cm
        return self


class SoilSet(DataBlock):
    profiles: list[SoilProfile] = Field(min_length=1)


class ClimateSeries(DataBlock):
    """Daily weather. ``et0_mm=None`` means the engine must compute ET0 from temperature.

    Scenario application (see scenario.apply_scenario) always clears et0_mm, because a
    stored ET0 would be stale after a temperature change.
    """

    start_date: date
    tmin_c: list[float]
    tmax_c: list[float]
    precip_mm: list[float]
    et0_mm: list[float] | None = None

    @model_validator(mode="after")
    def _aligned(self) -> "ClimateSeries":
        n = len(self.tmin_c)
        if n == 0:
            raise ValueError("climate series is empty")
        lengths = {len(self.tmax_c), len(self.precip_mm)} | (
            {len(self.et0_mm)} if self.et0_mm is not None else set()
        )
        if lengths != {n}:
            raise ValueError("all climate arrays must have the same length")
        if any(lo > hi for lo, hi in zip(self.tmin_c, self.tmax_c, strict=True)):
            raise ValueError("tmin must not exceed tmax")
        if any(p < 0 for p in self.precip_mm):
            raise ValueError("precipitation cannot be negative")
        return self


class CropSpec(ContractModel):
    id: str = Id
    name: str
    season_type: Literal["winter", "spring", "summer"]
    kc_ini: float = Field(gt=0)
    kc_mid: float = Field(gt=0)
    kc_end: float = Field(gt=0)
    stage_days: tuple[int, int, int, int] = Field(description="initial, development, mid, late")
    root_depth_max_m: float = Field(gt=0)
    depletion_p: float = Field(gt=0, lt=1, description="Fraction of TAW depletable w/o stress")
    ky: float = Field(gt=0, description="Yield response factor (FAO-33 style)")
    tbase_c: float


class CropCatalog(DataBlock):
    crops: list[CropSpec] = Field(min_length=1)


class ResourceRules(DataBlock):
    water_source: Literal["surface_quota", "groundwater_pumping"]
    seasonal_water_quota_mm: float | None = Field(default=None, gt=0)
    pumping_cost_per_mm: float | None = Field(default=None, gt=0)
    starting_budget: float = Field(gt=0, description="Game currency units")

    @model_validator(mode="after")
    def _rules(self) -> "ResourceRules":
        if self.water_source == "surface_quota" and self.seasonal_water_quota_mm is None:
            raise ValueError("surface_quota requires seasonal_water_quota_mm")
        if self.water_source == "groundwater_pumping" and self.pumping_cost_per_mm is None:
            raise ValueError("groundwater_pumping requires pumping_cost_per_mm")
        return self


class ObservationLayerSpec(DataBlock):
    layer: Literal["ndvi", "sar_backscatter", "sar_soil_moisture", "land_cover"]
    status: Literal["planned", "unverified", "verified_available"]
    note: str | None = None


class RegionPack(ContractModel):
    schema_version: Literal["0.1.0"] = "0.1.0"
    id: str = Id
    name: str
    description: str
    site: SiteGeometry
    parcels: ParcelSet
    soils: SoilSet
    climate: ClimateSeries
    crops: CropCatalog
    rules: ResourceRules
    observation_layers: list[ObservationLayerSpec]

    @model_validator(mode="after")
    def _references(self) -> "RegionPack":
        soil_ids = {s.id for s in self.soils.profiles}
        for p in self.parcels.parcels:
            if p.soil_id not in soil_ids:
                raise ValueError(f"parcel {p.id} references unknown soil {p.soil_id}")
        return self
