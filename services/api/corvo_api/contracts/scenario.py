"""ClimateScenario: a hypothetical applied ON TOP of a baseline, never written into it.

"Observed Earth" stays untouched: ``apply_scenario`` returns a NEW series whose provenance is
SIMULATED (or MOCK if the baseline was mock).
"""

from pydantic import Field, model_validator

from .provenance import DataBlock, DataKind, derive
from .region import ClimateSeries, Id

SCENARIO_KINDS = {DataKind.SIMULATED, DataKind.GAME_ASSUMPTION, DataKind.MOCK}


class ClimateScenario(DataBlock):
    id: str = Id
    label: str
    delta_t_c: float = Field(ge=-5, le=8, description="Added to tmin and tmax")
    precip_scale: float = Field(gt=0, le=3, description="Multiplier on daily precipitation")
    baseline_year: int | None = Field(default=None, description="Weather year to replay")
    seed: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def _never_observed(self) -> "ClimateScenario":
        if self.provenance.kind not in SCENARIO_KINDS:
            raise ValueError("a scenario is hypothetical; it cannot be labelled as real data")
        return self


def apply_scenario(series: ClimateSeries, scenario: ClimateScenario) -> ClimateSeries:
    """Return a scenario-modified copy of ``series`` (the input is not changed)."""
    prov = derive(
        DataKind.SIMULATED,
        source=f"Scenario '{scenario.label}' applied to baseline",
        generator="corvo_api.contracts.scenario.apply_scenario",
        parents=[series.provenance, scenario.provenance],
        notes=(
            f"delta_t_c={scenario.delta_t_c:+}, precip_scale={scenario.precip_scale}; "
            "et0 cleared: engine must recompute it from the modified temperatures"
        ),
    )
    return ClimateSeries(
        provenance=prov,
        start_date=series.start_date,
        tmin_c=[t + scenario.delta_t_c for t in series.tmin_c],
        tmax_c=[t + scenario.delta_t_c for t in series.tmax_c],
        precip_mm=[p * scenario.precip_scale for p in series.precip_mm],
        et0_mm=None,
    )
