from datetime import datetime
from decimal import Decimal

import pytest

from fundamental_analysis.models.financials import FinancialObservation
from fundamental_analysis.models.period import Period
from fundamental_analysis.models.stock import Exchange, Stock


@pytest.fixture
def reliance() -> Stock:
    return Stock(symbol="RELIANCE", name="Reliance Industries Limited", exchange=Exchange.NSE)


def test_financial_observation_preserves_fact_context(reliance: Stock) -> None:
    observation = FinancialObservation(
        stock=reliance,
        metric="revenue",
        value=Decimal("1000.00"),
        period=Period.annual(2025),
        source="provider_x",
        currency="INR",
        retrieved_at=datetime(2026, 9, 22, 10, 0),
    )

    assert observation.metric == "revenue"
    assert observation.period == Period.annual(2025)
    assert observation.source == "provider_x"


def test_financial_observation_allows_an_unavailable_value(reliance: Stock) -> None:
    observation = FinancialObservation(
        stock=reliance,
        metric="interest_expense",
        value=None,
        period=Period.annual(2025),
        source="provider_x",
    )

    assert observation.value is None


@pytest.mark.parametrize("field,value", [("metric", ""), ("period", "FY2025"), ("source", "")])
def test_financial_observation_rejects_blank_required_text(
    reliance: Stock,
    field: str,
    value: str,
) -> None:
    values = {
        "stock": reliance,
        "metric": "revenue",
        "value": Decimal("1000"),
        "period": Period.annual(2025),
        "source": "provider_x",
    }
    values[field] = value

    error_type = TypeError if field == "period" else ValueError
    with pytest.raises(error_type, match=field):
        FinancialObservation(**values)
