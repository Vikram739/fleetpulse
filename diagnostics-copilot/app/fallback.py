def generic_fallback_explanation(fault_code: str) -> tuple[str, str]:
    explanation = (
        f"We could not reach the diagnostics assistant right now to explain fault code "
        f"{fault_code} in detail. This code indicates the vehicle reported an issue that "
        f"needs attention."
    )
    next_step = "Have a technician inspect the vehicle and check the fault code against the service manual."
    return explanation, next_step
