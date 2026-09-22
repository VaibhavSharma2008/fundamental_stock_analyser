from decimal import Decimal

from fundamental_analysis.analysis.metric_calculator import (
    MetricCalculator,
    calculate_average_balance,
    calculate_cagr,
    calculate_growth,
    calculate_margin,
    calculate_ratio,
)
from fundamental_analysis.models.metrics import MetricStatus
from fundamental_analysis.models.period import Period


def test_metric_calculator_exposes_the_required_category_methods() -> None:
    calculator = MetricCalculator()

    for method_name in (
        "profitability",
        "growth",
        "margins",
        "leverage",
        "efficiency",
        "liquidity",
        "valuation",
        "cash_flow_quality",
        "ownership",
        "market_metrics",
        "red_flags",
    ):
        assert callable(getattr(calculator, method_name))


def test_calculation_primitives_return_structured_results() -> None:
    period = Period.annual(2025)

    growth = calculate_growth(Decimal("1200"), Decimal("1000"), name="growth", period=period)
    cagr = calculate_cagr(Decimal("1728"), Decimal("1000"), 3, name="cagr", period=period)
    margin = calculate_margin(Decimal("200"), Decimal("1000"), name="margin", period=period)
    ratio = calculate_ratio(Decimal("3"), Decimal("2"), name="ratio", period=period)
    average = calculate_average_balance(Decimal("100"), Decimal("200"), name="equity", period=period)

    assert growth.value == Decimal("20.0")
    assert cagr.value == Decimal("20.0")
    assert margin.value == Decimal("20.0")
    assert ratio.value == Decimal("1.5")
    assert average.value == Decimal("150")


def test_primitives_never_turn_missing_or_zero_denominators_into_zero() -> None:
    period = Period.annual(2025)

    missing = calculate_growth(None, Decimal("100"), name="growth", period=period)
    undefined = calculate_ratio(Decimal("1"), Decimal("0"), name="ratio", period=period)
    invalid = calculate_growth(float("nan"), Decimal("100"), name="growth", period=period)

    assert missing.status is MetricStatus.MISSING
    assert missing.value is None
    assert undefined.status is MetricStatus.UNDEFINED
    assert undefined.value is None
    assert invalid.status is MetricStatus.INVALID
    assert invalid.value is None
