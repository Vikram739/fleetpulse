import logging
from typing import Optional

from app.config import settings
from app.models import TelemetryContext

logger = logging.getLogger("diagnostics-copilot.llm")

PROMPT_TEMPLATE = """You are a vehicle diagnostics assistant helping a fleet operator understand a fault code.

Fault code: {fault_code}
Recent telemetry: {telemetry_summary}

Respond in exactly this format, with no extra commentary:
Explanation: <one or two plain language sentences explaining what this fault code means>
Next Step: <one concrete, actionable next step for the fleet operator>
"""


def summarize_telemetry(context: Optional[TelemetryContext]) -> str:
    if context is None:
        return "no recent telemetry available"
    parts = []
    if context.speed is not None:
        parts.append(f"speed {context.speed} km/h")
    if context.battery_percent is not None:
        parts.append(f"battery {context.battery_percent}%")
    if context.firmware_version is not None:
        parts.append(f"firmware {context.firmware_version}")
    return ", ".join(parts) if parts else "no recent telemetry available"


def build_prompt(fault_code: str, context: Optional[TelemetryContext]) -> str:
    return PROMPT_TEMPLATE.format(
        fault_code=fault_code, telemetry_summary=summarize_telemetry(context)
    )


def parse_llm_output(text: str) -> tuple[str, str]:
    explanation = ""
    next_step = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("explanation:"):
            explanation = stripped.split(":", 1)[1].strip()
        elif stripped.lower().startswith("next step:"):
            next_step = stripped.split(":", 1)[1].strip()
    if not explanation:
        explanation = text.strip()
    if not next_step:
        next_step = "Contact a technician to review this fault code."
    return explanation, next_step


def build_chat_model():
    if settings.uses_groq():
        from langchain_groq import ChatGroq

        return ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            timeout=settings.llm_timeout_seconds,
        )

    from langchain_ollama import ChatOllama

    return ChatOllama(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout=settings.llm_timeout_seconds,
    )


async def call_llm(fault_code: str, context: Optional[TelemetryContext]) -> tuple[str, str]:
    model = build_chat_model()
    prompt = build_prompt(fault_code, context)
    response = await model.ainvoke(prompt)
    content = response.content if hasattr(response, "content") else str(response)
    return parse_llm_output(content)
