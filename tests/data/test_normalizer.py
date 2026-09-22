from decimal import Decimal

import pytest

from fundamental_analysis.data.normalizer import (
    SIGN_CONVENTIONS,
    normalize_financial_field,
    normalize_financial_observation,
    normalize_missing_status,
    normalize_sign,
)
from fundamental_analysis.models.financials import FinancialObservation, ObservationStatus
from fundamental_analysis.models.period import Period
from fundamental_analysis.models.stock import Exchange, Stock


@pytest.mark.parametrize(
    ("provider_field", "canonical_field"),
    [
        ("revenue", "revenue"),
        ("totalRevenue", "revenue"),
        ("sales", "revenue"),
        ("pat", "pat"),
        ("netProfit", "pat"),
        ("profitAfterTax", "pat"),
    ],
)
def test_provider_aliases_map_to_canonical_fields(provider_field: str, canonical_field: str) -> None:
    assert normalize_financial_field(provider_field) == canonical_field


def test_unknown_provider_field_is_not_passed_to_calculation_code() -> None:
    assert normalize_financial_field("providerSpecificProfit") is None


def test_capex_and_interest_are_normalized_to_positive_outflows() -> None:
    assert normalize_sign("capex", Decimal("-500")) == Decimal("500")
    assert normalize_sign("interest_expense", Decimal("-20")) == Decimal("20")
    assert normalize_sign("cfo", Decimal("-150")) == Decimal("-150")
    assert SIGN_CONVENTIONS["capex"] == "positive cash outflow"


def test_normalized_observation_has_canonical_field_and_sign() -> None:
    stock = Stock("RELIANCE", "Reliance Industries Limited", Exchange.NSE)
    raw_observation = FinancialObservation(
        stock=stock,
        metric="capitalExpenditure",
        value=Decimal("-500"),
        period=Period.annual(2025),
        source="provider_x",
    )

    normalized = normalize_financial_observation(raw_observation)

    assert normalized.metric == "capex"
    assert normalized.value == Decimal("500")


def test_missing_value_keeps_an_explicit_missing_state() -> None:
    assert normalize_missing_status(None) is ObservationStatus.MISSING
    assert normalize_missing_status(Decimal("0")) is ObservationStatus.AVAILABLE
