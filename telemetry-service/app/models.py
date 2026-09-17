from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TelemetryPayload(BaseModel):
    vehicle_id: str = Field(min_length=1)
    speed: float = Field(ge=0, le=200)
    battery_percent: float = Field(ge=0, le=100)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    fault_code: Optional[str] = None
    firmware_version: str = Field(min_length=1)

    @field_validator("fault_code")
    @classmethod
    def normalize_fault_code(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped if stripped else None


class VehicleSnapshot(TelemetryPayload):
    server_received_at: float


class FleetSnapshotResponse(BaseModel):
    vehicle_count: int
    vehicles: list[VehicleSnapshot]
