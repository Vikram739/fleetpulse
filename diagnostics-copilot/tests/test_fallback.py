from app.fallback import generic_fallback_explanation


def test_fallback_includes_fault_code() -> None:
    explanation, next_step = generic_fallback_explanation("P0171")
    assert "P0171" in explanation
    assert next_step


def test_fallback_never_mentions_api_key() -> None:
    explanation, next_step = generic_fallback_explanation("P0171")
    assert "key" not in explanation.lower()
    assert "key" not in next_step.lower()
