import asyncio
import json
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.fallback import generic_fallback_explanation
from app.llm import call_llm
from app.models import DiagnoseRequest, DiagnoseResponse
from app.redis_client import redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("diagnostics-copilot")

app = FastAPI(title="FleetPulse Diagnostics Copilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    await redis_client.connect()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await redis_client.close()


@app.get("/health")
async def health() -> dict:
    redis_ok = await redis_client.ensure_connected()
    return {
        "status": "ok" if redis_ok else "degraded",
        "redis_connected": redis_ok,
        "llm_backend": "groq" if settings.uses_groq() else "ollama",
    }


def _cache_key(fault_code: str) -> str:
    return f"{settings.cache_key_prefix}:{fault_code}"


@app.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose(payload: DiagnoseRequest) -> DiagnoseResponse:
    fault_code = payload.fault_code
    cache_key = _cache_key(fault_code)

    cached = await redis_client.get(cache_key)
    if cached:
        try:
            cached_data = json.loads(cached)
            return DiagnoseResponse(
                fault_code=fault_code,
                explanation=cached_data["explanation"],
                suggested_next_step=cached_data["suggested_next_step"],
                source="cache",
            )
        except (json.JSONDecodeError, KeyError):
            logger.warning("Discarding corrupt cache entry for fault code %s", fault_code)

    try:
        explanation, next_step = await asyncio.wait_for(
            call_llm(fault_code, payload.telemetry_context),
            timeout=settings.llm_timeout_seconds,
        )
        source = "llm"
    except Exception as exc:
        logger.warning(
            "LLM call failed for fault code %s (%s), returning fallback explanation",
            fault_code,
            type(exc).__name__,
        )
        explanation, next_step = generic_fallback_explanation(fault_code)
        source = "fallback"

    if source == "llm":
        await redis_client.set(
            cache_key,
            json.dumps({"explanation": explanation, "suggested_next_step": next_step}),
            settings.cache_ttl_seconds,
        )

    return DiagnoseResponse(
        fault_code=fault_code,
        explanation=explanation,
        suggested_next_step=next_step,
        source=source,
    )
