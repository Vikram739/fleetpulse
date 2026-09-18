import pytest
from pydantic import ValidationError

from app.models import DiagnoseRequest


def test_valid_fault_code_is_normalized_to_uppercase() -> None:
    request = DiagnoseRequest(fault_code="p0171")
    assert request.fault_code == "P0171"


def test_blank_fault_code_raises() -> None:
    with pytest.raises(ValidationError):
        DiagnoseRequest(fault_code="   ")


def test_empty_fault_code_raises() -> None:
    with pytest.raises(ValidationError):
        DiagnoseRequest(fault_code="")


def test_telemetry_context_is_optional() -> None:
    request = DiagnoseRequest(fault_code="P0300")
    assert request.telemetry_context is None
