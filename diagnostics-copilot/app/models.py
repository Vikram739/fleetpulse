from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TelemetryContext(BaseModel):
    speed: Optional[float] = None
    battery_percent: Optional[float] = None
    firmware_version: Optional[str] = None


class DiagnoseRequest(BaseModel):
    fault_code: str = Field(min_length=1)
    telemetry_context: Optional[TelemetryContext] = None

    @field_validator("fault_code")
    @classmethod
    def fault_code_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("fault_code must not be blank")
        return stripped.upper()


class DiagnoseResponse(BaseModel):
    fault_code: str
    explanation: str
    suggested_next_step: str
    source: str
