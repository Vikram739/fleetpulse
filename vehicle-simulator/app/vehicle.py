import json
import random
from typing import Optional

from app.config import settings

FAULT_CODES: list[str] = ["P0171", "P0300", "P0420", "B1000", "C0035", "U0100"]


class Vehicle:
    def __init__(self, vehicle_id: str) -> None:
        self.vehicle_id: str = vehicle_id
        self.speed: float = random.uniform(0, 60)
        self.battery_percent: float = random.uniform(40, 100)
        self.latitude: float = random.uniform(
            settings.bounding_box_min_lat, settings.bounding_box_max_lat
        )
        self.longitude: float = random.uniform(
            settings.bounding_box_min_lon, settings.bounding_box_max_lon
        )
        self.firmware_version: str = random.choice(settings.firmware_versions)

    def _drift_speed(self) -> None:
        delta = random.uniform(-10, 10)
        self.speed = min(120, max(0, self.speed + delta))

    def _drain_battery(self) -> None:
        delta = random.uniform(-0.5, 0.05)
        self.battery_percent = min(100, max(0, self.battery_percent + delta))

    def _drift_position(self) -> None:
        lat_step = random.uniform(-0.001, 0.001)
        lon_step = random.uniform(-0.001, 0.001)
        self.latitude = min(
            settings.bounding_box_max_lat,
            max(settings.bounding_box_min_lat, self.latitude + lat_step),
        )
        self.longitude = min(
            settings.bounding_box_max_lon,
            max(settings.bounding_box_min_lon, self.longitude + lon_step),
        )

    def _maybe_fault_code(self) -> Optional[str]:
        if random.random() < settings.fault_code_probability:
            return random.choice(FAULT_CODES)
        return None

    def next_reading(self) -> dict:
        self._drift_speed()
        self._drain_battery()
        self._drift_position()
        return {
            "vehicle_id": self.vehicle_id,
            "speed": round(self.speed, 1),
            "battery_percent": round(self.battery_percent, 1),
            "latitude": round(self.latitude, 6),
            "longitude": round(self.longitude, 6),
            "fault_code": self._maybe_fault_code(),
            "firmware_version": self.firmware_version,
        }

    def next_reading_json(self) -> str:
        return json.dumps(self.next_reading())
