import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import repository, service
from app.config import settings
from app.db import database
from app.models import (
    FirmwareVersionCreate,
    FirmwareVersionResponse,
    ManualRollbackRequest,
    RolloutCreate,
    RolloutStatusResponse,
    RolloutSummaryResponse,
    VehicleCreate,
    VehicleResponse,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ota-service")

app = FastAPI(title="FleetPulse OTA Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RuntimeError)
async def database_unavailable_handler(request: Request, exc: RuntimeError) -> JSONResponse:
    logger.warning("Database unavailable while handling %s: %s", request.url.path, exc)
    return JSONResponse(status_code=503, content={"detail": "Database is currently unavailable"})


@app.on_event("startup")
async def on_startup() -> None:
    await database.connect()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await database.close()


@app.get("/health")
async def health() -> dict:
    db_ok = await database.is_connected()
    return {"status": "ok" if db_ok else "degraded", "database_connected": db_ok}


@app.post("/vehicles", response_model=VehicleResponse)
async def register_vehicle(payload: VehicleCreate) -> VehicleResponse:
    row = await repository.create_vehicle(payload.vehicle_id, payload.current_firmware_version)
    return VehicleResponse(**row)


@app.get("/vehicles", response_model=list[VehicleResponse])
async def get_vehicles() -> list[VehicleResponse]:
    rows = await repository.list_vehicles()
    return [VehicleResponse(**row) for row in rows]


@app.post("/firmware-versions", response_model=FirmwareVersionResponse)
async def register_firmware_version(payload: FirmwareVersionCreate) -> FirmwareVersionResponse:
    row = await repository.create_firmware_version(payload.version)
    return FirmwareVersionResponse(**row)


@app.get("/firmware-versions", response_model=list[FirmwareVersionResponse])
async def get_firmware_versions() -> list[FirmwareVersionResponse]:
    rows = await repository.list_firmware_versions()
    return [FirmwareVersionResponse(**row) for row in rows]


@app.post("/rollouts", response_model=RolloutSummaryResponse)
async def create_rollout(payload: RolloutCreate) -> RolloutSummaryResponse:
    return await service.create_rollout(payload)


@app.get("/rollouts", response_model=list[RolloutSummaryResponse])
async def get_rollouts() -> list[RolloutSummaryResponse]:
    return await service.list_rollouts()


@app.get("/rollouts/{rollout_id}", response_model=RolloutStatusResponse)
async def get_rollout(rollout_id: int) -> RolloutStatusResponse:
    return await service.get_rollout_status(rollout_id)


@app.post("/rollouts/{rollout_id}/advance", response_model=RolloutStatusResponse)
async def advance_rollout(rollout_id: int) -> RolloutStatusResponse:
    return await service.advance_rollout(rollout_id)


@app.post("/rollouts/{rollout_id}/rollback", response_model=RolloutStatusResponse)
async def rollback_rollout(
    rollout_id: int, payload: ManualRollbackRequest = ManualRollbackRequest()
) -> RolloutStatusResponse:
    logger.info("Manual rollback requested for rollout %s, reason: %s", rollout_id, payload.reason)
    return await service.manual_rollback(rollout_id)
