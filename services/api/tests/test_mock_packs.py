import json
import math

import pytest

from corvo_api.contracts import DataKind, RegionPack, data_status, iter_provenance
from corvo_api.mock_packs import CONFIGS, CUKUROVA, KONYA, build_mock_pack
from corvo_api.registry import load_pack, region_ids, summaries


@pytest.fixture(params=sorted(CONFIGS))
def pack(request) -> RegionPack:
    return build_mock_pack(CONFIGS[request.param])


def test_mock_packs_roundtrip_through_json(pack):
    again = RegionPack.model_validate_json(pack.model_dump_json())
    assert again == pack


def test_mock_data_is_never_labelled_as_real(pack):
    kinds = {p.kind for p in iter_provenance(pack)}
    assert kinds <= {DataKind.MOCK, DataKind.GAME_ASSUMPTION}
    assert data_status(pack) == "contains_mock"
    for p in iter_provenance(pack):
        assert p.dataset_id is None and p.retrieved_at is None


def test_geometry_blocks_are_mock(pack):
    assert pack.parcels.provenance.kind == DataKind.MOCK
    assert pack.soils.provenance.kind == DataKind.MOCK
    assert pack.climate.provenance.kind == DataKind.MOCK
    assert pack.crops.provenance.kind == DataKind.MOCK


def test_sar_layer_is_not_claimed_available(pack):
    sar = next(layer for layer in pack.observation_layers if layer.layer == "sar_backscatter")
    assert sar.status == "unverified"


def test_mock_climate_is_deterministic_and_plausible(pack):
    again = build_mock_pack(CONFIGS[pack.id])
    assert again.climate.tmax_c == pack.climate.tmax_c
    assert len(pack.climate.tmax_c) == 365
    assert all(lo <= hi for lo, hi in zip(pack.climate.tmin_c, pack.climate.tmax_c))


def test_regions_differ_in_climate_character_not_in_code():
    cuk, kon = build_mock_pack(CUKUROVA), build_mock_pack(KONYA)
    mean = lambda xs: sum(xs) / len(xs)  # noqa: E731
    jan = slice(0, 31)
    jul = slice(181, 212)
    # Continental Konya has the colder winter and larger seasonal swing.
    assert mean(kon.climate.tmax_c[jan]) < mean(cuk.climate.tmax_c[jan])
    swing = lambda p: mean(p.climate.tmax_c[jul]) - mean(p.climate.tmax_c[jan])  # noqa: E731
    assert swing(kon) > swing(cuk)
    # Resource rules differ through config: surface quota vs groundwater pumping.
    assert cuk.rules.water_source == "surface_quota"
    assert kon.rules.water_source == "groundwater_pumping"


def test_both_regions_share_one_schema_and_builder():
    assert type(build_mock_pack(CUKUROVA)) is type(build_mock_pack(KONYA)) is RegionPack


def test_parcel_areas_are_consistent_with_geometry(pack):
    for p in pack.parcels.parcels:
        lons = [x for x, _ in p.ring]
        lats = [y for _, y in p.ring]
        lat = math.radians(sum(lats) / len(lats))
        expect = (max(lons) - min(lons)) * 111.32 * math.cos(lat) * (max(lats) - min(lats)) * 110.57 * 100
        assert p.area_ha == pytest.approx(expect, rel=0.02)
        assert 5 < p.area_ha < 100


def test_registry_lists_both_pilots_with_mock_status():
    assert {"cukurova", "konya"} <= set(region_ids())
    assert all(s.data_status == "contains_mock" for s in summaries())


def test_registry_unknown_region_raises():
    with pytest.raises(KeyError):
        load_pack("atlantis")


def test_real_pack_on_disk_overrides_mock(tmp_path, pack):
    raw = pack.model_dump(mode="json")
    raw["name"] = "On-disk pack"
    (tmp_path / f"{pack.id}.json").write_text(json.dumps(raw), encoding="utf-8")
    assert load_pack(pack.id, tmp_path).name == "On-disk pack"


def test_invalid_pack_on_disk_is_rejected_not_silently_mocked(tmp_path, pack):
    raw = pack.model_dump(mode="json")
    raw["site"]["bbox"] = [10, 10, 5, 5]  # west > east
    (tmp_path / f"{pack.id}.json").write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(Exception):
        load_pack(pack.id, tmp_path)
