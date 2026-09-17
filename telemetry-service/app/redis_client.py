import asyncio
import logging

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger("telemetry-service.redis")


class RedisClient:
    def __init__(self) -> None:
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        delay = settings.redis_retry_base_delay
        attempt = 0
        while True:
            try:
                client = redis.from_url(
                    settings.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=settings.redis_socket_timeout,
                    socket_timeout=settings.redis_socket_timeout,
                )
                await asyncio.wait_for(client.ping(), timeout=settings.redis_socket_timeout)
                self._client = client
                logger.info("Connected to Redis")
                return
            except Exception as exc:
                attempt += 1
                if attempt > settings.redis_max_retries:
                    logger.error("Exceeded max Redis connection retries, giving up for now: %s", exc)
                    return
                logger.warning(
                    "Redis connection failed (attempt %s), retrying in %.1fs: %s",
                    attempt,
                    delay,
                    exc,
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, settings.redis_retry_max_delay)

    async def ensure_connected(self) -> bool:
        if self._client is None:
            await self.connect()
        if self._client is None:
            return False
        try:
            await asyncio.wait_for(self._client.ping(), timeout=settings.redis_socket_timeout)
            return True
        except Exception:
            logger.warning("Redis ping failed, attempting reconnect")
            self._client = None
            await self.connect()
            return self._client is not None

    async def publish(self, channel: str, message: str) -> bool:
        if not await self.ensure_connected():
            return False
        try:
            await asyncio.wait_for(
                self._client.publish(channel, message), timeout=settings.redis_socket_timeout
            )
            return True
        except Exception as exc:
            logger.warning("Redis publish failed: %s", exc)
            self._client = None
            return False

    async def hset(self, key: str, field: str, value: str) -> bool:
        if not await self.ensure_connected():
            return False
        try:
            await asyncio.wait_for(
                self._client.hset(key, field, value), timeout=settings.redis_socket_timeout
            )
            return True
        except Exception as exc:
            logger.warning("Redis hset failed: %s", exc)
            self._client = None
            return False

    async def hgetall(self, key: str) -> dict:
        if not await self.ensure_connected():
            return {}
        try:
            return await asyncio.wait_for(
                self._client.hgetall(key), timeout=settings.redis_socket_timeout
            )
        except Exception as exc:
            logger.warning("Redis hgetall failed: %s", exc)
            self._client = None
            return {}

    async def subscribe(self, channel: str):
        if not await self.ensure_connected():
            return None
        try:
            pubsub = self._client.pubsub()
            await asyncio.wait_for(pubsub.subscribe(channel), timeout=settings.redis_socket_timeout)
            return pubsub
        except Exception as exc:
            logger.warning("Redis subscribe failed: %s", exc)
            self._client = None
            return None

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None


redis_client = RedisClient()
