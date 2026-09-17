import pytest
from pydantic import ValidationError

from app.models import RolloutCreate


def test_default_stages_allowed_when_omitted() -> None:
    payload = RolloutCreate(firmware_version="1.2.0")
    assert payload.stages is None


def test_valid_custom_stages() -> None:
    payload = RolloutCreate(firmware_version="1.2.0", stages=[20, 60, 100])
    assert payload.stages == [20, 60, 100]


def test_stages_must_end_at_100() -> None:
    with pytest.raises(ValidationError):
        RolloutCreate(firmware_version="1.2.0", stages=[20, 60, 90])


def test_stages_must_be_increasing() -> None:
    with pytest.raises(ValidationError):
        RolloutCreate(firmware_version="1.2.0", stages=[60, 20, 100])


def test_stages_must_not_be_empty() -> None:
    with pytest.raises(ValidationError):
        RolloutCreate(firmware_version="1.2.0", stages=[])


def test_stages_out_of_range_rejected() -> None:
    with pytest.raises(ValidationError):
        RolloutCreate(firmware_version="1.2.0", stages=[0, 100])
