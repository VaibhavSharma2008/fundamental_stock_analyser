"""Structured transport model for core calculation results."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from .period import Period


class MetricStatus(str, Enum):
    """Availability state of a calculated metric."""

    AVAILABLE = "available"
    MISSING = "missing"
    NOT_APPLICABLE = "not_applicable"
    UNDEFINED = "undefined"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class MetricResult:
    """A calculated metric or an explicitly unavailable metric value."""

    name: str
    value: Decimal | None
    unit: str
    period: Period
    status: MetricStatus

    def __post_init__(self) -> None:
        _require_text(self.name, "name")
        _require_text(self.unit, "unit")
        _require_period(self.period)
        if not isinstance(self.status, MetricStatus):
            raise TypeError("status must be a MetricStatus")
        if self.status is MetricStatus.AVAILABLE and self.value is None:
            raise ValueError("available metrics require a value")
        if self.status is not MetricStatus.AVAILABLE and self.value is not None:
            raise ValueError("unavailable metrics must not contain a value")


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_period(value: Period) -> None:
    if not isinstance(value, Period):
        raise TypeError("period must be a Period")
