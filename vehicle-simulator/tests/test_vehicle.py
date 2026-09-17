import json

from app.config import settings
from app.vehicle import Vehicle


def test_reading_has_all_required_fields() -> None:
    vehicle = Vehicle("veh-001")
    reading = vehicle.next_reading()
    assert reading["vehicle_id"] == "veh-001"
    assert 0 <= reading["speed"] <= 120
    assert 0 <= reading["battery_percent"] <= 100
    assert reading["firmware_version"] in settings.firmware_versions


def test_position_stays_within_bounding_box() -> None:
    vehicle = Vehicle("veh-002")
    for _ in range(200):
        reading = vehicle.next_reading()
        assert settings.bounding_box_min_lat <= reading["latitude"] <= settings.bounding_box_max_lat
        assert settings.bounding_box_min_lon <= reading["longitude"] <= settings.bounding_box_max_lon


def test_speed_never_negative_or_over_limit() -> None:
    vehicle = Vehicle("veh-003")
    for _ in range(200):
        reading = vehicle.next_reading()
        assert 0 <= reading["speed"] <= 120


def test_reading_json_is_valid_json() -> None:
    vehicle = Vehicle("veh-004")
    payload = json.loads(vehicle.next_reading_json())
    assert payload["vehicle_id"] == "veh-004"


def test_fault_code_usually_none() -> None:
    vehicle = Vehicle("veh-005")
    readings = [vehicle.next_reading() for _ in range(500)]
    none_count = sum(1 for r in readings if r["fault_code"] is None)
    assert none_count > len(readings) * 0.8
