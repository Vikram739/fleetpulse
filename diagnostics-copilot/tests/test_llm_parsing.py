from app.llm import build_prompt, parse_llm_output, summarize_telemetry
from app.models import TelemetryContext


def test_parse_llm_output_standard_format() -> None:
    text = "Explanation: The battery sensor detected a fault.\nNext Step: Replace the battery sensor."
    explanation, next_step = parse_llm_output(text)
    assert explanation == "The battery sensor detected a fault."
    assert next_step == "Replace the battery sensor."


def test_parse_llm_output_missing_next_step_uses_default() -> None:
    text = "Explanation: The engine temperature is too high."
    explanation, next_step = parse_llm_output(text)
    assert explanation == "The engine temperature is too high."
    assert "technician" in next_step.lower()


def test_parse_llm_output_unstructured_text_falls_back_to_full_text() -> None:
    text = "This code just means something is wrong."
    explanation, next_step = parse_llm_output(text)
    assert explanation == text
    assert next_step


def test_summarize_telemetry_with_no_context() -> None:
    assert summarize_telemetry(None) == "no recent telemetry available"


def test_summarize_telemetry_with_partial_context() -> None:
    context = TelemetryContext(speed=42.0, battery_percent=None, firmware_version=None)
    summary = summarize_telemetry(context)
    assert "speed 42.0" in summary


def test_build_prompt_includes_fault_code() -> None:
    prompt = build_prompt("P0171", None)
    assert "P0171" in prompt
