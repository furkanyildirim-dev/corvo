from datetime import UTC, datetime

import pytest

from corvo_api.contracts import ClimateScenario, ClimateSeries, DataKind, Provenance, apply_scenario
from corvo_api.mock_packs import CUKUROVA, build_mock_pack

GA = Provenance(kind=DataKind.GAME_ASSUMPTION, source="player", generator="player")
SCEN = ClimateScenario(provenance=GA, id="hot-dry", label="+2C, -30% rain", delta_t_c=2.0, precip_scale=0.7)


def real_series() -> ClimateSeries:
    return ClimateSeries(
        provenance=Provenance(
            kind=DataKind.REANALYSIS, source="NASA POWER", dataset_id="POWER_DAILY",
            retrieved_at=datetime(2026, 10, 28, tzinfo=UTC),
        ),
        start_date="2020-01-01",
        tmin_c=[5.0, 6.0, 7.0],
        tmax_c=[15.0, 16.0, 17.0],
        precip_mm=[0.0, 10.0, 4.0],
        et0_mm=[1.0, 1.1, 1.2],
    )


def test_scenario_never_mutates_the_baseline():
    base = real_series()
    snapshot = base.model_dump()
    out = apply_scenario(base, SCEN)
    assert base.model_dump() == snapshot
    assert base.provenance.kind == DataKind.REANALYSIS
    assert out is not base


def test_scenario_applies_coupled_changes_and_clears_stale_et0():
    out = apply_scenario(real_series(), SCEN)
    assert out.tmin_c == [7.0, 8.0, 9.0]
    assert out.tmax_c == [17.0, 18.0, 19.0]
    assert out.precip_mm == pytest.approx([0.0, 7.0, 2.8])
    assert out.et0_mm is None  # a stored ET0 would be stale after +2C


def test_scenario_output_is_simulated_not_observed():
    out = apply_scenario(real_series(), SCEN)
    assert out.provenance.kind == DataKind.SIMULATED
    assert any("reanalysis:NASA POWER" in s for s in out.provenance.derived_from)


def test_mock_baseline_stays_mock_after_scenario():
    base = build_mock_pack(CUKUROVA).climate
    out = apply_scenario(base, SCEN)
    assert out.provenance.kind == DataKind.MOCK


def test_neutral_scenario_reproduces_values():
    neutral = ClimateScenario(provenance=GA, id="base", label="baseline", delta_t_c=0, precip_scale=1)
    base = real_series()
    out = apply_scenario(base, neutral)
    assert out.tmax_c == base.tmax_c and out.precip_mm == base.precip_mm
