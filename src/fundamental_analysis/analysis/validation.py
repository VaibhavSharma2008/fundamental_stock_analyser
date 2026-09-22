"""Validation helpers for normalized financial data."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import Enum
from numbers import Real

from fundamental_analysis.models.period import Period


class ValidationStatus(str, Enum):
    VALID = "valid"
    SUSPICIOUS = "suspicious"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class ValidationResult:
    status: ValidationStatus
    message: str | None = None


def validate_numeric_value(value: object) -> ValidationResult:
    """Validate a numeric fact without coercing missing data to zero."""

    if value is None:
        return ValidationResult(ValidationStatus.INVALID, "numeric value is missing")
    if isinstance(value, bool) or not isinstance(value, (Decimal, Real)):
        return ValidationResult(ValidationStatus.INVALID, "value must be numeric")
    if isinstance(value, Decimal) and not value.is_finite():
        return ValidationResult(ValidationStatus.INVALID, "value must be finite")
    if isinstance(value, float) and (value != value or value in {float("inf"), float("-inf")}):
        return ValidationResult(ValidationStatus.INVALID, "value must be finite")
    return ValidationResult(ValidationStatus.VALID)


def validate_period(period: object) -> ValidationResult:
    if not isinstance(period, Period):
        return ValidationResult(ValidationStatus.INVALID, "period must be a Period")
    return ValidationResult(ValidationStatus.VALID)


def validate_currency(currency: object) -> ValidationResult:
    if not isinstance(currency, str) or not currency.strip():
        return ValidationResult(ValidationStatus.INVALID, "currency is missing")
    if len(currency) != 3 or not currency.isalpha() or currency != currency.upper():
        return ValidationResult(ValidationStatus.INVALID, "currency must be an uppercase ISO code")
    return ValidationResult(ValidationStatus.VALID)


def validate_date(value: object) -> ValidationResult:
    if not isinstance(value, date):
        return ValidationResult(ValidationStatus.INVALID, "value must be a date")
    return ValidationResult(ValidationStatus.VALID)


def validate_percentage(value: object) -> ValidationResult:
    numeric_result = validate_numeric_value(value)
    if numeric_result.status is ValidationStatus.INVALID:
        return numeric_result

    decimal_value = _as_decimal(value)
    if decimal_value < 0:
        return ValidationResult(ValidationStatus.INVALID, "percentage cannot be negative")
    if decimal_value > 100:
        return ValidationResult(ValidationStatus.SUSPICIOUS, "percentage exceeds 100")
    return ValidationResult(ValidationStatus.VALID)


def _as_decimal(value: Decimal | Real) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError("value cannot be represented as Decimal") from error
