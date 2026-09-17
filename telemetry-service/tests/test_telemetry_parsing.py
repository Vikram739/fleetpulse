import pytest
from pydantic import ValidationError

from app.models import TelemetryPayload, VehicleSnapshot


def test_valid_payload_parses() -> None:
    payload = TelemetryPayload(
        vehicle_id="veh-1",
        speed=42.5,
        battery_percent=88,
        latitude=37.77,
        longitude=-122.41,
        fault_code=None,
        firmware_version="1.2.3",
    )
    assert payload.vehicle_id == "veh-1"
    assert payload.fault_code is None


def test_blank_fault_code_normalizes_to_none() -> None:
    payload = TelemetryPayload(
        vehicle_id="veh-1",
        speed=10,
        battery_percent=50,
        latitude=0,
        longitude=0,
        fault_code="   ",
        firmware_version="1.0.0",
    )
    assert payload.fault_code is None


def test_missing_required_field_raises() -> None:
    with pytest.raises(ValidationError):
        TelemetryPayload(
            speed=10,
            battery_percent=50,
            latitude=0,
            longitude=0,
            firmware_version="1.0.0",
        )


def test_out_of_range_speed_raises() -> None:
    with pytest.raises(ValidationError):
        TelemetryPayload(
            vehicle_id="veh-1",
            speed=999,
            battery_percent=50,
            latitude=0,
            longitude=0,
            firmware_version="1.0.0",
        )


def test_out_of_range_battery_raises() -> None:
    with pytest.raises(ValidationError):
        TelemetryPayload(
            vehicle_id="veh-1",
            speed=10,
            battery_percent=150,
            latitude=0,
            longitude=0,
            firmware_version="1.0.0",
        )


def test_snapshot_includes_server_received_at() -> None:
    payload = TelemetryPayload(
        vehicle_id="veh-1",
        speed=10,
        battery_percent=50,
        latitude=0,
        longitude=0,
        firmware_version="1.0.0",
    )
    snapshot = VehicleSnapshot(**payload.model_dump(), server_received_at=1234.5)
    assert snapshot.server_received_at == 1234.5
