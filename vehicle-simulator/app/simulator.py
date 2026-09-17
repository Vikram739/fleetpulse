import asyncio
import logging
import random

import websockets
from websockets.exceptions import WebSocketException

from app.config import settings
from app.vehicle import Vehicle

logger = logging.getLogger("vehicle-simulator")


async def run_vehicle(vehicle: Vehicle) -> None:
    delay = settings.reconnect_base_delay_seconds
    while True:
        try:
            async with websockets.connect(settings.telemetry_ws_url) as ws:
                logger.info("%s connected", vehicle.vehicle_id)
                delay = settings.reconnect_base_delay_seconds
                while True:
                    await ws.send(vehicle.next_reading_json())
                    interval = random.uniform(
                        settings.min_update_interval_seconds,
                        settings.max_update_interval_seconds,
                    )
                    await asyncio.sleep(interval)
        except (WebSocketException, OSError) as exc:
            logger.warning(
                "%s connection failed, retrying in %.1fs: %s", vehicle.vehicle_id, delay, exc
            )
            await asyncio.sleep(delay)
            delay = min(delay * 2, settings.reconnect_max_delay_seconds)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("%s unexpected error, retrying in %.1fs: %s", vehicle.vehicle_id, delay, exc)
            await asyncio.sleep(delay)
            delay = min(delay * 2, settings.reconnect_max_delay_seconds)


async def run_fleet() -> None:
    vehicles = [Vehicle(f"veh-{i + 1:03d}") for i in range(settings.vehicle_count)]
    logger.info("Starting simulator with %s vehicles targeting %s", len(vehicles), settings.telemetry_ws_url)
    await asyncio.gather(*(run_vehicle(vehicle) for vehicle in vehicles))
