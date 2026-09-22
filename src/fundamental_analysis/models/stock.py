"""Models for listed stocks, daily market data, and shareholding data."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from .period import Period, PeriodKind


class Exchange(str, Enum):
    """Supported Indian stock exchanges for the POC."""

    NSE = "NSE"
    BSE = "BSE"


@dataclass(frozen=True, slots=True)
class Stock:
    """A listed stock identified by its symbol and exchange."""

    symbol: str
    name: str
    exchange: Exchange
    isin: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.symbol, "symbol")
        _require_text(self.name, "name")


@dataclass(frozen=True, slots=True)
class MarketData:
    """A daily market-data observation kept separate from financial statements."""

    stock: Stock
    period: Period
    source: str
    price: Decimal | None = None
    trading_volume: int | None = None
    delivery_percentage: Decimal | None = None
    market_capitalization: Decimal | None = None
    week_52_high: Decimal | None = None
    week_52_low: Decimal | None = None
    volatility: Decimal | None = None
    currency: str | None = None

    def __post_init__(self) -> None:
        _require_period(self.period)
        if self.period.kind is not PeriodKind.DAILY:
            raise ValueError("market data requires a daily period")
        _require_text(self.source, "source")


@dataclass(frozen=True, slots=True)
class Shareholding:
    """A shareholding observation for one reported period."""

    stock: Stock
    period: Period
    source: str
    promoter_holding: Decimal | None = None
    promoter_pledge: Decimal | None = None
    fii_holding: Decimal | None = None
    dii_holding: Decimal | None = None

    def __post_init__(self) -> None:
        _require_period(self.period)
        _require_text(self.source, "source")


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_period(value: Period) -> None:
    if not isinstance(value, Period):
        raise TypeError("period must be a Period")
