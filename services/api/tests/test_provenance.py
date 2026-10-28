from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from corvo_api.contracts import (
    KIND_LABELS,
    DataKind,
    Provenance,
    data_status,
    derive,
    iter_provenance,
)

NOW = datetime(2026, 10, 28, tzinfo=UTC)


def real(kind=DataKind.REANALYSIS) -> Provenance:
    return Provenance(kind=kind, source="NASA POWER", dataset_id="POWER_DAILY", retrieved_at=NOW)


def mock() -> Provenance:
    return Provenance(kind=DataKind.MOCK, source="Synthetic", generator="tests")


def test_every_kind_has_a_label_and_mock_label_is_loud():
    assert set(KIND_LABELS) == {k.value for k in DataKind}
    assert KIND_LABELS[DataKind.MOCK] == "MOCK"
    assert len(set(KIND_LABELS.values())) == len(KIND_LABELS)  # no two kinds look alike


@pytest.mark.parametrize(
    "kind", [DataKind.OBSERVED, DataKind.REANALYSIS, DataKind.FORECAST, DataKind.MODEL_ESTIMATE]
)
def test_real_kinds_require_dataset_and_retrieval_time(kind):
    with pytest.raises(ValidationError):
        Provenance(kind=kind, source="NASA POWER")
    with pytest.raises(ValidationError):
        Provenance(kind=kind, source="NASA POWER", dataset_id="X")  # no retrieved_at
    assert real(kind).label == KIND_LABELS[kind]


def test_retrieval_time_must_be_timezone_aware():
    with pytest.raises(ValidationError):
        Provenance(
            kind=DataKind.OBSERVED, source="HLS", dataset_id="HLSS30", retrieved_at=datetime(2026, 1, 1)
        )


def test_real_data_cannot_claim_a_generator():
    with pytest.raises(ValidationError):
        Provenance(
            kind=DataKind.OBSERVED, source="HLS", dataset_id="X", retrieved_at=NOW, generator="me"
        )


def test_mock_cannot_pose_as_a_real_dataset():
    with pytest.raises(ValidationError):
        Provenance(kind=DataKind.MOCK, source="Fake POWER", generator="g", dataset_id="POWER_DAILY")
    with pytest.raises(ValidationError):
        Provenance(kind=DataKind.MOCK, source="Fake POWER", generator="g", retrieved_at=NOW)
    with pytest.raises(ValidationError):
        Provenance(kind=DataKind.MOCK, source="Fake POWER")  # generator missing


def test_generated_kinds_must_name_generator():
    for kind in (DataKind.GAME_ASSUMPTION, DataKind.SIMULATED):
        with pytest.raises(ValidationError):
            Provenance(kind=kind, source="whatever")


def test_provenance_is_immutable():
    p = mock()
    with pytest.raises(ValidationError):
        p.kind = DataKind.OBSERVED  # type: ignore[misc]


def test_derive_refuses_real_kinds():
    with pytest.raises(ValueError):
        derive(DataKind.OBSERVED, source="x y z", generator="g", parents=[real()])


def test_mock_taint_propagates_through_derive():
    out = derive(DataKind.SIMULATED, source="Scenario", generator="g", parents=[real(), mock()])
    assert out.kind == DataKind.MOCK
    clean = derive(DataKind.SIMULATED, source="Scenario", generator="g", parents=[real()])
    assert clean.kind == DataKind.SIMULATED
    assert "reanalysis:NASA POWER" in clean.derived_from


def test_data_status_and_iteration_find_nested_provenance():
    from corvo_api.mock_packs import CUKUROVA, build_mock_pack

    pack = build_mock_pack(CUKUROVA)
    kinds = {p.kind for p in iter_provenance(pack)}
    assert DataKind.MOCK in kinds and DataKind.GAME_ASSUMPTION in kinds
    assert data_status(pack) == "contains_mock"
    assert data_status(real()) == "no_mock"
