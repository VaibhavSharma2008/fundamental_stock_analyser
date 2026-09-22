from datetime import date
from decimal import Decimal

import pytest

from fundamental_analysis.models.period import Period
from fundamental_analysis.models.stock import Exchange, MarketData, Shareholding, Stock


@pytest.fixture
def reliance() -> Stock:
    return Stock(symbol="RELIANCE", name="Reliance Industries Limited", exchange=Exchange.NSE)


def test_stock_can_represent_a_listed_company() -> None:
    stock = Stock(
        symbol="RELIANCE",
        name="Reliance Industries Limited",
        exchange=Exchange.NSE,
        isin="INE002A01018",
    )

    assert stock.symbol == "RELIANCE"
    assert stock.exchange is Exchange.NSE


def test_stock_rejects_a_blank_symbol() -> None:
    with pytest.raises(ValueError, match="symbol"):
        Stock(symbol=" ", name="Reliance Industries Limited", exchange=Exchange.NSE)


def test_market_data_can_represent_daily_market_facts(reliance: Stock) -> None:
    market_data = MarketData(
        stock=reliance,
        period=Period.daily(date(2026, 9, 21)),
        source="provider_x",
        price=Decimal("1400.25"),
        trading_volume=1_250_000,
        delivery_percentage=Decimal("52.4"),
        currency="INR",
    )

    assert market_data.period == Period.daily(date(2026, 9, 21))
    assert market_data.price == Decimal("1400.25")


def test_market_data_rejects_a_blank_source(reliance: Stock) -> None:
    with pytest.raises(ValueError, match="source"):
        MarketData(stock=reliance, period=Period.daily(date(2026, 9, 21)), source="")


def test_shareholding_can_represent_quarterly_ownership(reliance: Stock) -> None:
    shareholding = Shareholding(
        stock=reliance,
        period=Period.quarterly(2026, 1),
        source="provider_x",
        promoter_holding=Decimal("50.13"),
        promoter_pledge=Decimal("0"),
        fii_holding=Decimal("21.45"),
        dii_holding=Decimal("14.10"),
    )

    assert shareholding.promoter_holding == Decimal("50.13")
    assert shareholding.period == Period.quarterly(2026, 1)


def test_shareholding_rejects_a_non_period_value(reliance: Stock) -> None:
    with pytest.raises(TypeError, match="period"):
        Shareholding(stock=reliance, period="Q1 FY2026", source="provider_x")
