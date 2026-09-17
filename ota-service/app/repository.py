from typing import Any, Optional

import asyncpg

from app.db import database


async def create_vehicle(vehicle_id: str, current_firmware_version: Optional[str]) -> dict:
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO vehicles (vehicle_id, current_firmware_version)
            VALUES ($1, $2)
            ON CONFLICT (vehicle_id)
            DO UPDATE SET current_firmware_version = EXCLUDED.current_firmware_version
            RETURNING vehicle_id, current_firmware_version
            """,
            vehicle_id,
            current_firmware_version,
        )
        return dict(row)


async def list_vehicles() -> list[dict]:
    async with database.pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT vehicle_id, current_firmware_version FROM vehicles ORDER BY vehicle_id"
        )
        return [dict(row) for row in rows]


async def list_vehicle_ids() -> list[str]:
    async with database.pool.acquire() as conn:
        rows = await conn.fetch("SELECT vehicle_id FROM vehicles ORDER BY vehicle_id")
        return [row["vehicle_id"] for row in rows]


async def create_firmware_version(version: str) -> dict:
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO firmware_versions (version)
            VALUES ($1)
            ON CONFLICT (version) DO UPDATE SET version = EXCLUDED.version
            RETURNING id, version
            """,
            version,
        )
        return dict(row)


async def list_firmware_versions() -> list[dict]:
    async with database.pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, version FROM firmware_versions ORDER BY id")
        return [dict(row) for row in rows]


async def get_firmware_version_by_name(version: str) -> Optional[dict]:
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, version FROM firmware_versions WHERE version = $1", version
        )
        return dict(row) if row else None


async def create_rollout(
    firmware_version_id: int, stages: list[int], failure_threshold_percent: float
) -> dict:
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO rollouts (firmware_version_id, stages, failure_threshold_percent)
            VALUES ($1, $2, $3)
            RETURNING id, firmware_version_id, stages, current_stage_index, status,
                      failure_threshold_percent, created_at, updated_at
            """,
            firmware_version_id,
            stages,
            failure_threshold_percent,
        )
        return dict(row)


async def list_rollouts() -> list[dict]:
    async with database.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT r.id, r.status, r.current_stage_index, r.stages, fv.version AS firmware_version
            FROM rollouts r
            JOIN firmware_versions fv ON fv.id = r.firmware_version_id
            ORDER BY r.id DESC
            """
        )
        return [dict(row) for row in rows]


async def get_rollout_with_lock(conn: asyncpg.Connection, rollout_id: int) -> Optional[dict]:
    row = await conn.fetchrow(
        """
        SELECT r.id, r.firmware_version_id, r.stages, r.current_stage_index, r.status,
               r.failure_threshold_percent, fv.version AS firmware_version
        FROM rollouts r
        JOIN firmware_versions fv ON fv.id = r.firmware_version_id
        WHERE r.id = $1
        FOR UPDATE
        """,
        rollout_id,
    )
    return dict(row) if row else None


async def get_rollout(rollout_id: int) -> Optional[dict]:
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT r.id, r.firmware_version_id, r.stages, r.current_stage_index, r.status,
                   r.failure_threshold_percent, fv.version AS firmware_version
            FROM rollouts r
            JOIN firmware_versions fv ON fv.id = r.firmware_version_id
            WHERE r.id = $1
            """,
            rollout_id,
        )
        return dict(row) if row else None


async def get_assigned_vehicle_ids(conn: asyncpg.Connection, rollout_id: int) -> set[str]:
    rows = await conn.fetch(
        "SELECT vehicle_id FROM rollout_batches WHERE rollout_id = $1", rollout_id
    )
    return {row["vehicle_id"] for row in rows}


async def insert_batch_rows(
    conn: asyncpg.Connection,
    rollout_id: int,
    vehicle_statuses: dict[str, str],
    stage_index: int,
    stage_percent: int,
) -> None:
    if not vehicle_statuses:
        return
    await conn.executemany(
        """
        INSERT INTO rollout_batches (rollout_id, vehicle_id, stage_index, stage_percent, status)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (rollout_id, vehicle_id) DO NOTHING
        """,
        [
            (rollout_id, vehicle_id, stage_index, stage_percent, status)
            for vehicle_id, status in vehicle_statuses.items()
        ],
    )


async def update_rollout_stage(
    conn: asyncpg.Connection, rollout_id: int, stage_index: int, status: str
) -> None:
    await conn.execute(
        """
        UPDATE rollouts
        SET current_stage_index = $2, status = $3, updated_at = now()
        WHERE id = $1
        """,
        rollout_id,
        stage_index,
        status,
    )


async def update_rollout_status(conn: asyncpg.Connection, rollout_id: int, status: str) -> None:
    await conn.execute(
        "UPDATE rollouts SET status = $2, updated_at = now() WHERE id = $1",
        rollout_id,
        status,
    )


async def get_batches_for_rollout(rollout_id: int) -> list[dict]:
    async with database.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT vehicle_id, stage_index, stage_percent, status
            FROM rollout_batches
            WHERE rollout_id = $1
            ORDER BY vehicle_id
            """,
            rollout_id,
        )
        return [dict(row) for row in rows]
