from datetime import datetime
from decimal import Decimal

import pytest

from fundamental_analysis.models.financials import FinancialObservation, ObservationStatus
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
        status=ObservationStatus.MISSING,
    )

    assert observation.value is None
    assert observation.status is ObservationStatus.MISSING


@pytest.mark.parametrize(
    "metric",
    [
        "revenue",
        "ebitda",
        "ebit",
        "pat",
        "eps",
        "equity",
        "debt",
        "cash",
        "receivables",
        "inventory",
        "payables",
        "cfo",
        "capex",
        "interest_expense",
        "shares_outstanding",
    ],
)
def test_financial_observation_can_represent_supported_underlying_facts(
    reliance: Stock,
    metric: str,
) -> None:
    observation = FinancialObservation(
        stock=reliance,
        metric=metric,
        value=Decimal("1"),
        period=Period.annual(2025),
        source="provider_x",
    )

    assert observation.metric == metric


def test_financial_observation_requires_an_explicit_missing_status(reliance: Stock) -> None:
    with pytest.raises(ValueError, match="available observations"):
        FinancialObservation(
            stock=reliance,
            metric="revenue",
            value=None,
            period=Period.annual(2025),
            source="provider_x",
        )


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
