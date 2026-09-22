"""Structured transport model for core calculation results."""

from dataclasses import dataclass
from decimal import Decimal

from .period import Period


@dataclass(frozen=True, slots=True)
class MetricResult:
    """A calculated metric or an explicitly unavailable metric value.

    FA-004 will formalize the permitted status values and their validation.
    This foundational model keeps the metric's value, unit, and period separate
    from any CLI or UI presentation.
    """

    name: str
    value: Decimal | None
    unit: str
    period: Period
    status: str

    def __post_init__(self) -> None:
        _require_text(self.name, "name")
        _require_text(self.unit, "unit")
        _require_period(self.period)
        _require_text(self.status, "status")


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_period(value: Period) -> None:
    if not isinstance(value, Period):
        raise TypeError("period must be a Period")
