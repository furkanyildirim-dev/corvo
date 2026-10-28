import pytest
from pydantic import ValidationError

from corvo_api.contracts import (
    ClimateScenario,
    DataKind,
    EngineInfo,
    IrrigationPolicy,
    ManagementPlan,
    ParcelSeasonPlan,
    Provenance,
    RegionPack,
    SeasonPlan,
    SimState,
    uncovered_numeric_models,
    validate_plan_against_region,
)
from corvo_api.mock_packs import CONFIGS, build_mock_pack

GA = Provenance(kind=DataKind.GAME_ASSUMPTION, source="player", generator="player")


def make_plan(region="cukurova", crop="wheat", parcel="p1") -> ManagementPlan:
    return ManagementPlan(
        provenance=GA,
        id="plan-a",
        region_id=region,
        label="A",
        seasons=[
            SeasonPlan(
                season=1,
                parcels=[
                    ParcelSeasonPlan(
                        parcel_id=parcel,
                        crop_id=crop,
                        sowing_doy=300,
                        irrigation=IrrigationPolicy(strategy="rainfed"),
                    )
                ],
            )
        ],
    )


@pytest.fixture(params=sorted(CONFIGS))
def pack(request) -> RegionPack:
    return build_mock_pack(CONFIGS[request.param])


def test_every_data_carrying_node_sits_under_a_provenance_block(pack):
    assert uncovered_numeric_models(pack) == []


def test_uncovered_numeric_detector_actually_detects():
    class Naked(ParcelSeasonPlan):  # a numeric model outside any DataBlock
        pass

    naked = Naked(parcel_id="p1", crop_id=None, irrigation=IrrigationPolicy(strategy="rainfed"))
    assert uncovered_numeric_models(naked) == ["Naked"]


def test_extra_fields_are_rejected():
    with pytest.raises(ValidationError):
        ClimateScenario(
            provenance=GA, id="s", label="x", delta_t_c=0, precip_scale=1, bogus=1  # type: ignore
        )


def test_scenario_cannot_be_labelled_observed():
    real = Provenance(
        kind=DataKind.OBSERVED, source="HLS", dataset_id="HLSS30",
        retrieved_at="2026-10-28T00:00:00+00:00",
    )
    with pytest.raises(ValidationError):
        ClimateScenario(provenance=real, id="s", label="x", delta_t_c=2, precip_scale=1)


def test_scenario_bounds():
    for kwargs in ({"delta_t_c": 20, "precip_scale": 1}, {"delta_t_c": 0, "precip_scale": 0}):
        with pytest.raises(ValidationError):
            ClimateScenario(provenance=GA, id="s", label="x", **kwargs)


def test_irrigation_strategy_requirements():
    with pytest.raises(ValidationError):
        IrrigationPolicy(strategy="fixed_depth", depth_mm=30)  # missing interval
    with pytest.raises(ValidationError):
        IrrigationPolicy(strategy="deficit_threshold", depth_mm=30)  # missing trigger
    assert IrrigationPolicy(strategy="rainfed").depth_mm is None


def test_sown_crop_needs_sowing_date_and_fallow_does_not():
    with pytest.raises(ValidationError):
        ParcelSeasonPlan(parcel_id="p1", crop_id="wheat", irrigation=IrrigationPolicy(strategy="rainfed"))
    ParcelSeasonPlan(parcel_id="p1", crop_id=None, irrigation=IrrigationPolicy(strategy="rainfed"))


def test_seasons_must_be_consecutive():
    plan = make_plan()
    bad = plan.model_dump()
    bad["seasons"][0]["season"] = 2
    with pytest.raises(ValidationError):
        ManagementPlan.model_validate(bad)


def test_plan_cross_check_against_region(pack):
    assert validate_plan_against_region(make_plan(region=pack.id), pack) == []
    problems = validate_plan_against_region(make_plan(region=pack.id, crop="rice", parcel="zz"), pack)
    assert any("unknown parcel" in p for p in problems)
    assert any("not in catalog" in p for p in problems)
    assert validate_plan_against_region(make_plan(region="other"), pack)


def test_region_rejects_dangling_soil_reference(pack):
    raw = pack.model_dump(mode="json")
    raw["parcels"]["parcels"][0]["soil_id"] = "nope"
    with pytest.raises(ValidationError):
        RegionPack.model_validate(raw)


def test_region_rejects_unclosed_parcel_ring(pack):
    raw = pack.model_dump(mode="json")
    raw["parcels"]["parcels"][0]["ring"][-1] = [0.0, 0.0]
    with pytest.raises(ValidationError):
        RegionPack.model_validate(raw)


def test_water_rules_match_source(pack):
    raw = pack.model_dump(mode="json")
    raw["rules"]["water_source"] = (
        "groundwater_pumping" if pack.rules.water_source == "surface_quota" else "surface_quota"
    )
    raw["rules"]["seasonal_water_quota_mm"] = None
    raw["rules"]["pumping_cost_per_mm"] = None
    with pytest.raises(ValidationError):
        RegionPack.model_validate(raw)


def test_simstate_engine_must_match_provenance():
    kwargs = dict(
        run_id="r1", region_id="cukurova", plan_id="plan-a", scenario_id="base",
        days=[], summaries=[],
    )
    mock_prov = Provenance(kind=DataKind.MOCK, source="mock engine", generator="tests")
    sim_prov = Provenance(kind=DataKind.SIMULATED, source="AquaCrop", generator="aquacrop")
    SimState(provenance=mock_prov, engine=EngineInfo(name="m", version="0", is_mock=True), **kwargs)
    SimState(provenance=sim_prov, engine=EngineInfo(name="a", version="1", is_mock=False), **kwargs)
    with pytest.raises(ValidationError):  # mock engine output may not look scientific
        SimState(provenance=sim_prov, engine=EngineInfo(name="m", version="0", is_mock=True), **kwargs)
    with pytest.raises(ValidationError):  # real engine output may not hide as mock either
        SimState(provenance=mock_prov, engine=EngineInfo(name="a", version="1", is_mock=False), **kwargs)
