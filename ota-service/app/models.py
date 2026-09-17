from typing import Optional

from pydantic import BaseModel, Field, field_validator


class VehicleCreate(BaseModel):
    vehicle_id: str = Field(min_length=1)
    current_firmware_version: Optional[str] = None


class VehicleResponse(BaseModel):
    vehicle_id: str
    current_firmware_version: Optional[str]


class FirmwareVersionCreate(BaseModel):
    version: str = Field(min_length=1)


class FirmwareVersionResponse(BaseModel):
    id: int
    version: str


class RolloutCreate(BaseModel):
    firmware_version: str = Field(min_length=1)
    stages: Optional[list[int]] = None
    failure_threshold_percent: Optional[float] = Field(default=None, ge=0, le=100)

    @field_validator("stages")
    @classmethod
    def validate_stages(cls, value: Optional[list[int]]) -> Optional[list[int]]:
        if value is None:
            return None
        if not value:
            raise ValueError("stages must not be empty")
        if any(v <= 0 or v > 100 for v in value):
            raise ValueError("stages must be between 1 and 100")
        if list(value) != sorted(value):
            raise ValueError("stages must be in increasing order")
        if value[-1] != 100:
            raise ValueError("last stage must be 100")
        return value


class BatchVehicleStatus(BaseModel):
    vehicle_id: str
    stage_index: int
    stage_percent: int
    status: str


class RolloutStatusResponse(BaseModel):
    id: int
    firmware_version: str
    stages: list[int]
    current_stage_index: int
    current_stage_percent: Optional[int]
    status: str
    failure_threshold_percent: float
    total_vehicles: int
    assigned_count: int
    success_count: int
    failed_count: int
    unresponsive_count: int
    rollback_count: int
    pending_count: int
    percent_complete: float
    vehicles: list[BatchVehicleStatus]


class RolloutSummaryResponse(BaseModel):
    id: int
    firmware_version: str
    status: str
    current_stage_index: int
    stages: list[int]


class ManualRollbackRequest(BaseModel):
    reason: Optional[str] = None
