import random
from typing import Optional

from fastapi import HTTPException

from app import repository
from app.config import settings
from app.db import database
from app.models import (
    BatchVehicleStatus,
    RolloutCreate,
    RolloutStatusResponse,
    RolloutSummaryResponse,
)
from app.rollout_logic import (
    FAILED,
    PENDING,
    ROLLBACK,
    ROLLOUT_COMPLETED,
    ROLLOUT_HALTED,
    ROLLOUT_IN_PROGRESS,
    ROLLOUT_ROLLED_BACK,
    SUCCESS,
    TERMINAL_ROLLOUT_STATUSES,
    UNRESPONSIVE,
    compute_failure_rate,
    is_final_stage,
    select_new_batch_vehicle_ids,
    should_trigger_rollback,
    simulate_outcomes,
)


async def create_rollout(payload: RolloutCreate) -> RolloutSummaryResponse:
    firmware = await repository.get_firmware_version_by_name(payload.firmware_version)
    if firmware is None:
        raise HTTPException(
            status_code=404,
            detail=f"Firmware version '{payload.firmware_version}' does not exist",
        )
    stages = payload.stages or settings.default_rollout_stages
    threshold = (
        payload.failure_threshold_percent
        if payload.failure_threshold_percent is not None
        else settings.default_failure_threshold_percent
    )
    row = await repository.create_rollout(firmware["id"], stages, threshold)
    return RolloutSummaryResponse(
        id=row["id"],
        firmware_version=payload.firmware_version,
        status=row["status"],
        current_stage_index=row["current_stage_index"],
        stages=list(row["stages"]),
    )


async def list_rollouts() -> list[RolloutSummaryResponse]:
    rows = await repository.list_rollouts()
    return [
        RolloutSummaryResponse(
            id=row["id"],
            firmware_version=row["firmware_version"],
            status=row["status"],
            current_stage_index=row["current_stage_index"],
            stages=list(row["stages"]),
        )
        for row in rows
    ]


def _build_status_response(rollout: dict, batches: list[dict], total_vehicles: int) -> RolloutStatusResponse:
    stages = list(rollout["stages"])
    current_stage_index = rollout["current_stage_index"]
    current_stage_percent = (
        stages[current_stage_index] if 0 <= current_stage_index < len(stages) else None
    )

    success_count = sum(1 for b in batches if b["status"] == SUCCESS)
    failed_count = sum(1 for b in batches if b["status"] == FAILED)
    unresponsive_count = sum(1 for b in batches if b["status"] == UNRESPONSIVE)
    rollback_count = sum(1 for b in batches if b["status"] == ROLLBACK)
    pending_count = sum(1 for b in batches if b["status"] == PENDING)
    assigned_count = len(batches)

    percent_complete = 0.0
    if total_vehicles > 0:
        resolved = success_count + failed_count + rollback_count
        percent_complete = round(100 * resolved / total_vehicles, 1)
    elif rollout["status"] == ROLLOUT_COMPLETED:
        percent_complete = 100.0

    return RolloutStatusResponse(
        id=rollout["id"],
        firmware_version=rollout["firmware_version"],
        stages=stages,
        current_stage_index=current_stage_index,
        current_stage_percent=current_stage_percent,
        status=rollout["status"],
        failure_threshold_percent=rollout["failure_threshold_percent"],
        total_vehicles=total_vehicles,
        assigned_count=assigned_count,
        success_count=success_count,
        failed_count=failed_count,
        unresponsive_count=unresponsive_count,
        rollback_count=rollback_count,
        pending_count=pending_count,
        percent_complete=percent_complete,
        vehicles=[
            BatchVehicleStatus(
                vehicle_id=b["vehicle_id"],
                stage_index=b["stage_index"],
                stage_percent=b["stage_percent"],
                status=b["status"],
            )
            for b in batches
        ],
    )


async def get_rollout_status(rollout_id: int) -> RolloutStatusResponse:
    rollout = await repository.get_rollout(rollout_id)
    if rollout is None:
        raise HTTPException(status_code=404, detail=f"Rollout {rollout_id} not found")
    batches = await repository.get_batches_for_rollout(rollout_id)
    total_vehicles = len(await repository.list_vehicle_ids())
    return _build_status_response(rollout, batches, total_vehicles)


async def advance_rollout(
    rollout_id: int, rng: Optional[random.Random] = None
) -> RolloutStatusResponse:
    async with database.pool.acquire() as conn:
        async with conn.transaction():
            rollout = await repository.get_rollout_with_lock(conn, rollout_id)
            if rollout is None:
                raise HTTPException(status_code=404, detail=f"Rollout {rollout_id} not found")
            if rollout["status"] in TERMINAL_ROLLOUT_STATUSES:
                raise HTTPException(
                    status_code=409,
                    detail=f"Rollout {rollout_id} is already {rollout['status']} and cannot advance",
                )

            all_vehicle_ids = await repository.list_vehicle_ids()
            stages = list(rollout["stages"])
            next_stage_index = rollout["current_stage_index"] + 1

            if next_stage_index >= len(stages):
                await repository.update_rollout_status(conn, rollout_id, ROLLOUT_COMPLETED)
            else:
                stage_percent = stages[next_stage_index]
                already_assigned = await repository.get_assigned_vehicle_ids(conn, rollout_id)
                new_vehicle_ids = select_new_batch_vehicle_ids(
                    all_vehicle_ids, already_assigned, stage_percent
                )

                if new_vehicle_ids:
                    outcomes = simulate_outcomes(
                        new_vehicle_ids,
                        settings.simulated_success_probability,
                        settings.simulated_failure_probability,
                        settings.simulated_unresponsive_probability,
                        rng=rng,
                    )
                    await repository.insert_batch_rows(
                        conn, rollout_id, outcomes, next_stage_index, stage_percent
                    )
                    failure_rate = compute_failure_rate(outcomes)
                else:
                    failure_rate = 0.0

                if new_vehicle_ids and should_trigger_rollback(
                    failure_rate, rollout["failure_threshold_percent"]
                ):
                    remaining_ids = [
                        v
                        for v in all_vehicle_ids
                        if v not in already_assigned and v not in new_vehicle_ids
                    ]
                    if remaining_ids:
                        rollback_statuses = {v: ROLLBACK for v in remaining_ids}
                        await repository.insert_batch_rows(
                            conn, rollout_id, rollback_statuses, next_stage_index, stage_percent
                        )
                    await repository.update_rollout_stage(
                        conn, rollout_id, next_stage_index, ROLLOUT_HALTED
                    )
                elif is_final_stage(next_stage_index, stages):
                    await repository.update_rollout_stage(
                        conn, rollout_id, next_stage_index, ROLLOUT_COMPLETED
                    )
                else:
                    await repository.update_rollout_stage(
                        conn, rollout_id, next_stage_index, ROLLOUT_IN_PROGRESS
                    )

            updated_rollout = await repository.get_rollout_with_lock(conn, rollout_id)
            batches = await conn.fetch(
                """
                SELECT vehicle_id, stage_index, stage_percent, status
                FROM rollout_batches WHERE rollout_id = $1 ORDER BY vehicle_id
                """,
                rollout_id,
            )
            total_vehicles = len(all_vehicle_ids)
            return _build_status_response(
                updated_rollout, [dict(b) for b in batches], total_vehicles
            )


async def manual_rollback(rollout_id: int) -> RolloutStatusResponse:
    async with database.pool.acquire() as conn:
        async with conn.transaction():
            rollout = await repository.get_rollout_with_lock(conn, rollout_id)
            if rollout is None:
                raise HTTPException(status_code=404, detail=f"Rollout {rollout_id} not found")
            if rollout["status"] in TERMINAL_ROLLOUT_STATUSES:
                raise HTTPException(
                    status_code=409,
                    detail=f"Rollout {rollout_id} is already {rollout['status']} and cannot be rolled back",
                )

            all_vehicle_ids = await repository.list_vehicle_ids()
            already_assigned = await repository.get_assigned_vehicle_ids(conn, rollout_id)
            remaining_ids = [v for v in all_vehicle_ids if v not in already_assigned]
            if remaining_ids:
                stage_index = rollout["current_stage_index"] if rollout["current_stage_index"] >= 0 else 0
                stage_percent = (
                    rollout["stages"][stage_index] if stage_index < len(rollout["stages"]) else 100
                )
                rollback_statuses = {v: ROLLBACK for v in remaining_ids}
                await repository.insert_batch_rows(
                    conn, rollout_id, rollback_statuses, stage_index, stage_percent
                )

            await repository.update_rollout_status(conn, rollout_id, ROLLOUT_ROLLED_BACK)

            updated_rollout = await repository.get_rollout_with_lock(conn, rollout_id)
            batches = await conn.fetch(
                """
                SELECT vehicle_id, stage_index, stage_percent, status
                FROM rollout_batches WHERE rollout_id = $1 ORDER BY vehicle_id
                """,
                rollout_id,
            )
            total_vehicles = len(all_vehicle_ids)
            return _build_status_response(
                updated_rollout, [dict(b) for b in batches], total_vehicles
            )
