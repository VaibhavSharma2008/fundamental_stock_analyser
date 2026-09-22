from datetime import date
from decimal import Decimal

import pytest

from fundamental_analysis.analysis.validation import (
    ValidationStatus,
    validate_currency,
    validate_date,
    validate_numeric_value,
    validate_percentage,
    validate_period,
)
from fundamental_analysis.models.period import Period


@pytest.mark.parametrize("value", [Decimal("10"), 10, 10.5])
def test_validate_numeric_value_accepts_finite_numbers(value: object) -> None:
    assert validate_numeric_value(value).status is ValidationStatus.VALID


@pytest.mark.parametrize("value", [None, "10", True, float("nan"), Decimal("NaN")])
def test_validate_numeric_value_rejects_invalid_values_without_defaulting_to_zero(value: object) -> None:
    result = validate_numeric_value(value)

    assert result.status is ValidationStatus.INVALID
    assert result.message is not None


def test_validation_checks_period_currency_and_date() -> None:
    assert validate_period(Period.annual(2025)).status is ValidationStatus.VALID
    assert validate_period("FY2025").status is ValidationStatus.INVALID
    assert validate_currency("INR").status is ValidationStatus.VALID
    assert validate_currency(None).status is ValidationStatus.INVALID
    assert validate_date(date(2026, 9, 22)).status is ValidationStatus.VALID
    assert validate_date("2026-09-22").status is ValidationStatus.INVALID


def test_validate_percentage_flags_suspicious_and_invalid_representations() -> None:
    assert validate_percentage(Decimal("54.2")).status is ValidationStatus.VALID
    assert validate_percentage(Decimal("101")).status is ValidationStatus.SUSPICIOUS
    assert validate_percentage(Decimal("-1")).status is ValidationStatus.INVALID
