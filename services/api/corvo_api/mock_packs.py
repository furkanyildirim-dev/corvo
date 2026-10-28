"""MOCK region packs. Every number here is a placeholder, NOT data.

Both pilot regions are built by the SAME function from a config object, which is the M6
acceptance principle in miniature: regions differ in data/config, never in engine code.

What is labelled how:
- Parcel shapes, soils, weather, crop parameters: MOCK (generated here, not real).
- Site coordinates: GAME_ASSUMPTION (chosen by hand, approximate, to be verified in M1).
- Water-resource rules: GAME_ASSUMPTION (balance parameters; no NASA product measures them).
- Observation-layer availability: GAME_ASSUMPTION ("planned"/"unverified" status).
"""

import math
import random
from dataclasses import dataclass
from datetime import date

from .contracts import (
    ClimateSeries,
    CropCatalog,
    CropSpec,
    DataKind,
    ObservationLayerSpec,
    Parcel,
    ParcelSet,
    Provenance,
    RegionPack,
    ResourceRules,
    SiteGeometry,
    SoilLayer,
    SoilProfile,
    SoilSet,
)

GENERATOR = "corvo_api.mock_packs v0.1"


def _mock(source: str, notes: str) -> Provenance:
    return Provenance(kind=DataKind.MOCK, source=source, generator=GENERATOR, notes=notes)


def _assumption(source: str, notes: str) -> Provenance:
    return Provenance(
        kind=DataKind.GAME_ASSUMPTION, source=source, generator="corvo-team", notes=notes
    )


@dataclass(frozen=True)
class MockClimateParams:
    tmax_mean_c: float
    tmax_amp_c: float
    diurnal_range_c: float
    rain_peak_doy: int  # day of year with the highest rain probability
    rain_prob_base: float
    rain_prob_amp: float
    rain_mean_mm: float


@dataclass(frozen=True)
class MockRegionConfig:
    id: str
    name: str
    description: str
    center: tuple[float, float]  # lon, lat
    half_width_deg: float
    local_epsg: int
    climate: MockClimateParams
    crop_ids: tuple[str, ...]
    soil_ids: tuple[str, ...]
    water_source: str
    seasonal_water_quota_mm: float | None
    pumping_cost_per_mm: float | None
    starting_budget: float
    sar_status: str = "unverified"


# Placeholder crop parameters written from memory of typical FAO-56 magnitudes.
# They MUST be replaced from the FAO-56 tables (and checked against AquaCrop) in M7.
_CROPS = {
    "wheat": ("Wheat", "winter", 0.30, 1.15, 0.30, (30, 140, 40, 30), 1.5, 0.55, 1.15, 0.0),
    "barley": ("Barley", "winter", 0.30, 1.15, 0.25, (20, 25, 60, 30), 1.5, 0.55, 1.0, 0.0),
    "maize": ("Maize", "summer", 0.30, 1.20, 0.35, (25, 40, 40, 30), 1.7, 0.55, 1.25, 8.0),
    "cotton": ("Cotton", "summer", 0.35, 1.15, 0.70, (30, 50, 55, 45), 1.5, 0.65, 0.85, 12.0),
    "soybean": ("Soybean", "summer", 0.40, 1.15, 0.50, (20, 30, 60, 25), 1.3, 0.50, 0.85, 8.0),
    "sugar_beet": ("Sugar beet", "spring", 0.35, 1.20, 0.70, (30, 45, 90, 15), 1.2, 0.55, 1.0, 4.0),
    "chickpea": ("Chickpea", "spring", 0.40, 1.15, 0.35, (20, 30, 40, 20), 1.0, 0.45, 0.8, 5.0),
}

_SOILS = {
    "clay_loam": ("Clay loam (mock)", 0.17, 0.32, 0.45, 40.0),
    "loam": ("Loam (mock)", 0.10, 0.24, 0.43, 120.0),
    "silty_clay": ("Silty clay (mock)", 0.22, 0.38, 0.48, 15.0),
}

CUKUROVA = MockRegionConfig(
    id="cukurova",
    name="Çukurova / Aşağı Seyhan (MOCK)",
    description="Pilot A. Approximate site; parcels, soils and weather are placeholders.",
    center=(35.35, 36.95),
    half_width_deg=0.12,
    local_epsg=32636,
    climate=MockClimateParams(28.0, 9.0, 11.0, 15, 0.20, 0.18, 8.0),
    crop_ids=("wheat", "maize", "cotton", "soybean"),
    soil_ids=("clay_loam", "silty_clay"),
    water_source="surface_quota",
    seasonal_water_quota_mm=500.0,
    pumping_cost_per_mm=None,
    starting_budget=10_000.0,
)

KONYA = MockRegionConfig(
    id="konya",
    name="Konya Kapalı Havzası (MOCK)",
    description="Pilot B. Approximate site; parcels, soils and weather are placeholders.",
    center=(32.85, 37.55),
    half_width_deg=0.15,
    local_epsg=32636,
    climate=MockClimateParams(18.5, 14.0, 14.0, 90, 0.10, 0.07, 6.0),
    crop_ids=("wheat", "barley", "sugar_beet", "maize", "chickpea"),
    soil_ids=("loam", "clay_loam"),
    water_source="groundwater_pumping",
    seasonal_water_quota_mm=None,
    pumping_cost_per_mm=1.4,
    starting_budget=8_000.0,
)

CONFIGS: dict[str, MockRegionConfig] = {c.id: c for c in (CUKUROVA, KONYA)}


def _parcel_area_ha(w: float, s: float, e: float, n: float) -> float:
    lat = math.radians((s + n) / 2)
    km_x = (e - w) * 111.32 * math.cos(lat)
    km_y = (n - s) * 110.57
    return round(km_x * km_y * 100, 2)


def _parcels(cfg: MockRegionConfig) -> list[Parcel]:
    lon, lat = cfg.center
    cols, rows = 3, 2
    cell_w, cell_h = 0.0055, 0.0042  # degrees (~490 m x 465 m, ~23 ha); gaps leave room for roads
    gap = 0.0015
    x0 = lon - (cols * cell_w + (cols - 1) * gap) / 2
    y0 = lat - (rows * cell_h + (rows - 1) * gap) / 2
    out: list[Parcel] = []
    for r in range(rows):
        for c in range(cols):
            w = x0 + c * (cell_w + gap)
            s = y0 + r * (cell_h + gap)
            e, n = w + cell_w, s + cell_h
            idx = r * cols + c
            out.append(
                Parcel(
                    id=f"p{idx + 1}",
                    name=f"Parcel {idx + 1}",
                    ring=[(w, s), (e, s), (e, n), (w, n), (w, s)],
                    area_ha=_parcel_area_ha(w, s, e, n),
                    soil_id=cfg.soil_ids[idx % len(cfg.soil_ids)],
                )
            )
    return out


def _soil_profile(sid: str) -> SoilProfile:
    name, wp, fc, sat, ksat = _SOILS[sid]
    # Slightly heavier subsoil. Placeholder values.
    layers = [
        SoilLayer(top_cm=0, bottom_cm=30, theta_wp=wp, theta_fc=fc, theta_sat=sat, ksat_mm_day=ksat),
        SoilLayer(
            top_cm=30, bottom_cm=60, theta_wp=wp + 0.01, theta_fc=fc + 0.01, theta_sat=sat,
            ksat_mm_day=ksat * 0.7,
        ),
        SoilLayer(
            top_cm=60, bottom_cm=100, theta_wp=wp + 0.02, theta_fc=fc + 0.02, theta_sat=sat,
            ksat_mm_day=ksat * 0.5,
        ),
    ]
    return SoilProfile(id=sid, name=name, layers=layers)


def _climate(cfg: MockRegionConfig, seed: int = 42, days: int = 365) -> ClimateSeries:
    p = cfg.climate
    rng = random.Random(f"{cfg.id}:{seed}")
    start = date(2001, 1, 1)  # arbitrary placeholder year; not a real weather year
    tmin: list[float] = []
    tmax: list[float] = []
    rain: list[float] = []
    for d in range(days):
        doy = d + 1
        season = math.cos(2 * math.pi * (doy - 200) / 365)  # warmest ~ doy 200
        hi = p.tmax_mean_c + p.tmax_amp_c * season + rng.gauss(0, 2.0)
        lo = hi - p.diurnal_range_c - rng.uniform(0, 2.0)
        prob = p.rain_prob_base + p.rain_prob_amp * math.cos(
            2 * math.pi * (doy - p.rain_peak_doy) / 365
        )
        amount = rng.expovariate(1 / p.rain_mean_mm) if rng.random() < prob else 0.0
        tmax.append(round(hi, 2))
        tmin.append(round(lo, 2))
        rain.append(round(amount, 2))
    return ClimateSeries(
        provenance=_mock(
            "Synthetic daily weather",
            "Seeded sinusoid + noise shaped like the region's climate type. Not a real year. "
            "ET0 omitted: the engine computes it from temperature.",
        ),
        start_date=start,
        tmin_c=tmin,
        tmax_c=tmax,
        precip_mm=rain,
        et0_mm=None,
    )


def _crop_specs(ids: tuple[str, ...]) -> list[CropSpec]:
    specs = []
    for cid in ids:
        name, stype, kc_i, kc_m, kc_e, stages, root, p, ky, tbase = _CROPS[cid]
        specs.append(
            CropSpec(
                id=cid, name=name, season_type=stype, kc_ini=kc_i, kc_mid=kc_m, kc_end=kc_e,
                stage_days=stages, root_depth_max_m=root, depletion_p=p, ky=ky, tbase_c=tbase,
            )
        )
    return specs


def build_mock_pack(cfg: MockRegionConfig) -> RegionPack:
    lon, lat = cfg.center
    h = cfg.half_width_deg
    return RegionPack(
        id=cfg.id,
        name=cfg.name,
        description=cfg.description,
        site=SiteGeometry(
            provenance=_assumption(
                "Hand-picked approximate site",
                "Approximate; exact AOI to be verified in the M1 coordinate probe.",
            ),
            bbox=(lon - h, lat - h, lon + h, lat + h),
            center=(lon, lat),
            local_epsg=cfg.local_epsg,
        ),
        parcels=ParcelSet(
            provenance=_mock(
                "Synthetic rectangular parcels",
                "Not real field boundaries. Real parcels will be digitised in M1/M2.",
            ),
            parcels=_parcels(cfg),
        ),
        soils=SoilSet(
            provenance=_mock(
                "Synthetic soil profiles",
                "Placeholder hydraulic properties; real source planned: SoilGrids (model estimate).",
            ),
            profiles=[_soil_profile(s) for s in cfg.soil_ids],
        ),
        climate=_climate(cfg),
        crops=CropCatalog(
            provenance=_mock(
                "Placeholder crop parameters",
                "Written from memory of typical FAO-56 magnitudes; replace from FAO-56 in M7.",
            ),
            crops=_crop_specs(cfg.crop_ids),
        ),
        rules=ResourceRules(
            provenance=_assumption(
                "Game balance parameters",
                "Water quota / pumping cost are game parameters; no NASA product measures them.",
            ),
            water_source=cfg.water_source,  # type: ignore[arg-type]
            seasonal_water_quota_mm=cfg.seasonal_water_quota_mm,
            pumping_cost_per_mm=cfg.pumping_cost_per_mm,
            starting_budget=cfg.starting_budget,
        ),
        observation_layers=[
            ObservationLayerSpec(
                provenance=_assumption("Planned layer", "Real NDVI integration is milestone M3."),
                layer="ndvi",
                status="planned",
            ),
            ObservationLayerSpec(
                provenance=_assumption("Unverified layer", "SAR coverage not yet checked."),
                layer="sar_backscatter",
                status=cfg.sar_status,  # type: ignore[arg-type]
                note="NISAR coverage for this AOI is NOT verified.",
            ),
        ],
    )
