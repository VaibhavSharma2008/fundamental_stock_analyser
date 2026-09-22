from datetime import date
from decimal import Decimal

import pytest

from fundamental_analysis.analysis.metric_calculator import MetricCalculator
from fundamental_analysis.models.financials import FinancialObservation, ObservationStatus
from fundamental_analysis.models.metrics import MetricStatus
from fundamental_analysis.models.period import Period
from fundamental_analysis.models.stock import Exchange, Stock


RELIANCE = Stock("RELIANCE", "Reliance Industries Limited", Exchange.NSE)


def observation(metric: str, value: Decimal, period: Period) -> FinancialObservation:
    return FinancialObservation(
        stock=RELIANCE,
        metric=metric,
        value=value,
        period=period,
        source="provider_x",
    )


def test_revenue_growth_returns_twenty_percent() -> None:
    result = MetricCalculator().revenue_growth(
        observation("revenue", Decimal("1200"), Period.annual(2025)),
        observation("revenue", Decimal("1000"), Period.annual(2024)),
    )

    assert result.value == Decimal("20.0")
    assert result.status is MetricStatus.AVAILABLE


def test_revenue_growth_with_a_zero_or_negative_base_is_undefined() -> None:
    calculator = MetricCalculator()
    current = observation("revenue", Decimal("1200"), Period.annual(2025))

    zero_base = calculator.revenue_growth(current, observation("revenue", Decimal("0"), Period.annual(2024)))
    negative_base = calculator.revenue_growth(current, observation("revenue", Decimal("-100"), Period.annual(2024)))

    assert zero_base.status is MetricStatus.UNDEFINED
    assert negative_base.status is MetricStatus.UNDEFINED


def test_revenue_growth_with_a_missing_input_is_missing() -> None:
    result = MetricCalculator().revenue_growth(
        FinancialObservation(
            stock=RELIANCE,
            metric="revenue",
            value=None,
            period=Period.annual(2025),
            source="provider_x",
            status=ObservationStatus.MISSING,
        ),
        observation("revenue", Decimal("1000"), Period.annual(2024)),
    )

    assert result.status is MetricStatus.MISSING


def test_growth_rejects_observations_from_different_stocks() -> None:
    other_stock = Stock("TCS", "Tata Consultancy Services Limited", Exchange.NSE)
    result = MetricCalculator().revenue_growth(
        observation("revenue", Decimal("1200"), Period.annual(2025)),
        FinancialObservation(
            stock=other_stock,
            metric="revenue",
            value=Decimal("1000"),
            period=Period.annual(2024),
            source="provider_x",
        ),
    )

    assert result.status is MetricStatus.INVALID


def test_ebitda_pat_and_eps_growth_reuse_the_same_growth_policy() -> None:
    calculator = MetricCalculator()
    period = Period.annual(2025)
    prior_period = Period.annual(2024)

    results = (
        calculator.ebitda_growth(observation("ebitda", Decimal("120"), period), observation("ebitda", Decimal("100"), prior_period)),
        calculator.pat_growth(observation("pat", Decimal("60"), period), observation("pat", Decimal("50"), prior_period)),
        calculator.eps_growth(observation("eps", Decimal("12"), period), observation("eps", Decimal("10"), prior_period)),
    )

    assert all(result.value == Decimal("20.0") for result in results)


def test_ttm_growth_requires_distinct_ttm_periods() -> None:
    result = MetricCalculator().ttm_growth(
        observation("revenue", Decimal("1320"), Period.ttm(date(2026, 3, 31))),
        observation("revenue", Decimal("1200"), Period.ttm(date(2025, 3, 31))),
    )

    assert result.value == Decimal("10.0")
    assert result.period.kind.value == "ttm"


def test_ttm_growth_rejects_annual_inputs() -> None:
    result = MetricCalculator().ttm_growth(
        observation("revenue", Decimal("1200"), Period.annual(2025)),
        observation("revenue", Decimal("1000"), Period.annual(2024)),
    )

    assert result.status is MetricStatus.INVALID


def test_quarterly_sequential_growth_requires_adjacent_quarters() -> None:
    result = MetricCalculator().quarterly_sequential_growth(
        observation("revenue", Decimal("120"), Period.quarterly(2026, 1)),
        observation("revenue", Decimal("100"), Period.quarterly(2025, 4)),
    )

    assert result.value == Decimal("20.0")
    assert result.name == "revenue_quarterly_sequential_growth"


def test_quarterly_sequential_growth_rejects_non_adjacent_quarters() -> None:
    result = MetricCalculator().quarterly_sequential_growth(
        observation("revenue", Decimal("120"), Period.quarterly(2025, 3)),
        observation("revenue", Decimal("100"), Period.quarterly(2025, 1)),
    )

    assert result.status is MetricStatus.INVALID


def test_three_year_cagr_handles_meaningful_and_nonmeaningful_cases() -> None:
    calculator = MetricCalculator()
    available = calculator.three_year_cagr(
        observation("revenue", Decimal("1728"), Period.annual(2025)),
        observation("revenue", Decimal("1000"), Period.annual(2022)),
    )
    undefined = calculator.three_year_cagr(
        observation("pat", Decimal("100"), Period.annual(2025)),
        observation("pat", Decimal("-50"), Period.annual(2022)),
    )

    assert available.value == Decimal("20.0")
    assert undefined.status is MetricStatus.UNDEFINED


@pytest.mark.parametrize(
    ("current", "beginning", "status"),
    [
        (Decimal("1728"), Decimal("1000"), MetricStatus.AVAILABLE),
        (Decimal("100"), Decimal("0"), MetricStatus.UNDEFINED),
        (Decimal("100"), Decimal("-50"), MetricStatus.UNDEFINED),
        (Decimal("-50"), Decimal("100"), MetricStatus.UNDEFINED),
        (Decimal("-100"), Decimal("-50"), MetricStatus.UNDEFINED),
    ],
)
def test_three_year_cagr_defines_all_required_sign_transitions(
    current: Decimal,
    beginning: Decimal,
    status: MetricStatus,
) -> None:
    result = MetricCalculator().three_year_cagr(
        observation("pat", current, Period.annual(2025)),
        observation("pat", beginning, Period.annual(2022)),
    )

    assert result.status is status
