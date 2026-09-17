import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

import asyncpg

from app.config import settings

logger = logging.getLogger("ota-service.db")

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class Database:
    def __init__(self) -> None:
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        delay = settings.db_retry_base_delay
        attempt = 0
        while True:
            try:
                self._pool = await asyncio.wait_for(
                    asyncpg.create_pool(
                        settings.database_url,
                        min_size=1,
                        max_size=10,
                        timeout=settings.db_query_timeout,
                        command_timeout=settings.db_query_timeout,
                    ),
                    timeout=settings.db_query_timeout,
                )
                logger.info("Connected to Postgres")
                await self._run_migrations()
                return
            except Exception as exc:
                attempt += 1
                if attempt > settings.db_max_retries:
                    logger.error("Exceeded max Postgres connection retries, giving up for now: %s", exc)
                    self._pool = None
                    return
                logger.warning(
                    "Postgres connection failed (attempt %s), retrying in %.1fs: %s",
                    attempt,
                    delay,
                    exc,
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, settings.db_retry_max_delay)

    async def _run_migrations(self) -> None:
        if self._pool is None:
            return
        schema_sql = SCHEMA_PATH.read_text()
        async with self._pool.acquire() as conn:
            await conn.execute(schema_sql)
        logger.info("Schema migration applied")

    async def is_connected(self) -> bool:
        if self._pool is None:
            await self.connect()
        if self._pool is None:
            return False
        try:
            async with self._pool.acquire() as conn:
                await asyncio.wait_for(conn.execute("SELECT 1"), timeout=settings.db_query_timeout)
            return True
        except Exception:
            logger.warning("Postgres health check failed")
            return False

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("Database pool is not initialized")
        return self._pool

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None


database = Database()
