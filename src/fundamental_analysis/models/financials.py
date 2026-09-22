"""Models for normalized, underlying financial facts."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum

from .period import Period
from .stock import Stock


class ObservationStatus(str, Enum):
    """Availability state for a normalized financial fact."""

    AVAILABLE = "available"
    MISSING = "missing"
    NOT_APPLICABLE = "not_applicable"
    UNDEFINED = "undefined"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class FinancialObservation:
    """One provider-sourced financial fact for a stock and reported period.

    ``period`` preserves its frequency and fiscal semantics through ``Period``.
    """

    stock: Stock
    metric: str
    value: Decimal | None
    period: Period
    source: str
    status: ObservationStatus = ObservationStatus.AVAILABLE
    currency: str | None = None
    retrieved_at: datetime | None = None

    def __post_init__(self) -> None:
        _require_text(self.metric, "metric")
        _require_period(self.period)
        _require_text(self.source, "source")
        if not isinstance(self.status, ObservationStatus):
            raise TypeError("status must be an ObservationStatus")
        if self.status is ObservationStatus.AVAILABLE and self.value is None:
            raise ValueError("available observations require a value")
        if self.status is not ObservationStatus.AVAILABLE and self.value is not None:
            raise ValueError("unavailable observations must not contain a value")


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_period(value: Period) -> None:
    if not isinstance(value, Period):
        raise TypeError("period must be a Period")
