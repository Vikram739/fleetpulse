import asyncio
import json
import logging
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.config import settings
from app.models import FleetSnapshotResponse, TelemetryPayload, VehicleSnapshot
from app.redis_client import redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("telemetry-service")

app = FastAPI(title="FleetPulse Telemetry Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

_last_accepted_at: dict[str, float] = {}


@app.on_event("startup")
async def on_startup() -> None:
    await redis_client.connect()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await redis_client.close()


@app.get("/health")
async def health() -> dict:
    redis_ok = await redis_client.ensure_connected()
    return {"status": "ok" if redis_ok else "degraded", "redis_connected": redis_ok}


@app.get("/fleet", response_model=FleetSnapshotResponse)
async def get_fleet_snapshot() -> FleetSnapshotResponse:
    raw = await redis_client.hgetall(settings.snapshot_key)
    vehicles: list[VehicleSnapshot] = []
    for value in raw.values():
        try:
            vehicles.append(VehicleSnapshot.model_validate_json(value))
        except ValidationError as exc:
            logger.warning("Skipping corrupt snapshot entry: %s", exc)
    return FleetSnapshotResponse(vehicle_count=len(vehicles), vehicles=vehicles)


def _is_rate_limited(vehicle_id: str) -> bool:
    now = time.monotonic()
    last = _last_accepted_at.get(vehicle_id)
    if last is not None and (now - last) < settings.min_message_interval_seconds:
        return True
    _last_accepted_at[vehicle_id] = now
    return False


@app.websocket("/ws/telemetry")
async def telemetry_websocket(websocket: WebSocket) -> None:
    await websocket.accept()
    logger.info("Vehicle telemetry connection opened")
    try:
        while True:
            raw_message = await websocket.receive_text()
            server_received_at = time.time()

            try:
                data = json.loads(raw_message)
            except json.JSONDecodeError as exc:
                logger.warning("Dropping malformed JSON payload: %s", exc)
                continue

            try:
                payload = TelemetryPayload.model_validate(data)
            except ValidationError as exc:
                logger.warning("Dropping invalid telemetry payload: %s", exc)
                continue

            if _is_rate_limited(payload.vehicle_id):
                logger.debug("Rate limiting messages from %s", payload.vehicle_id)
                continue

            snapshot = VehicleSnapshot(
                **payload.model_dump(),
                server_received_at=server_received_at,
            )
            snapshot_json = snapshot.model_dump_json()

            await redis_client.publish(settings.redis_channel, snapshot_json)
            await redis_client.hset(settings.snapshot_key, payload.vehicle_id, snapshot_json)

    except WebSocketDisconnect:
        logger.info("Vehicle telemetry connection closed")


@app.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket) -> None:
    await websocket.accept()
    logger.info("Dashboard connection opened")

    snapshot = await get_fleet_snapshot()
    try:
        await websocket.send_text(
            json.dumps({"type": "snapshot", "vehicles": [v.model_dump() for v in snapshot.vehicles]})
        )
    except WebSocketDisconnect:
        logger.info("Dashboard connection closed before snapshot sent")
        return

    disconnect_task = asyncio.ensure_future(websocket.receive_text())
    pubsub = None
    delay = settings.redis_retry_base_delay
    try:
        while True:
            if disconnect_task.done():
                disconnect_task.result()
                break

            if pubsub is None:
                pubsub = await redis_client.subscribe(settings.redis_channel)
                if pubsub is None:
                    await asyncio.sleep(min(delay, 1.0))
                    delay = min(delay * 2, settings.redis_retry_max_delay)
                    continue
                delay = settings.redis_retry_base_delay

            try:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            except Exception as exc:
                logger.warning("Dashboard pubsub read failed, resubscribing: %s", exc)
                pubsub = None
                continue

            if message is not None and message.get("type") == "message":
                await websocket.send_text(
                    json.dumps({"type": "telemetry", "data": json.loads(message["data"])})
                )
    except WebSocketDisconnect:
        logger.info("Dashboard connection closed")
    finally:
        disconnect_task.cancel()
        if pubsub is not None:
            try:
                await pubsub.close()
            except Exception:
                pass
