"""Period-aware metric calculation primitives and growth calculations."""

from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from numbers import Real

from fundamental_analysis.models.financials import FinancialObservation, ObservationStatus
from fundamental_analysis.models.metrics import MetricResult, MetricStatus
from fundamental_analysis.models.period import Period, PeriodKind
from fundamental_analysis.models.stock import MarketData, Shareholding

Numeric = Decimal | Real


class MetricCalculator:
    """Central home for POC calculation categories.

    Categories without finalized metrics return no results until their dedicated
    Jira story is implemented. They never produce placeholder numeric values.
    """

    def profitability(self, financials: Sequence[FinancialObservation]) -> dict[str, MetricResult]:
        return {}

    def growth(self, financials: Sequence[FinancialObservation]) -> dict[str, MetricResult]:
        return {}

    def margins(self, financials: Sequence[FinancialObservation]) -> dict[str, MetricResult]:
        return {}

    def leverage(self, financials: Sequence[FinancialObservation]) -> dict[str, MetricResult]:
        return {}

    def efficiency(self, financials: Sequence[FinancialObservation]) -> dict[str, MetricResult]:
        return {}

    def liquidity(self, financials: Sequence[FinancialObservation]) -> dict[str, MetricResult]:
        return {}

    def valuation(
        self,
        financials: Sequence[FinancialObservation],
        market_data: Sequence[MarketData],
    ) -> dict[str, MetricResult]:
        return {}

    def cash_flow_quality(self, financials: Sequence[FinancialObservation]) -> dict[str, MetricResult]:
        return {}

    def ownership(self, shareholding: Shareholding) -> dict[str, MetricResult]:
        return {}

    def market_metrics(self, market_data: Sequence[MarketData]) -> dict[str, MetricResult]:
        return {}

    def red_flags(self, financials: Sequence[FinancialObservation]) -> dict[str, MetricResult]:
        return {}

    def revenue_growth(
        self,
        current: FinancialObservation,
        previous: FinancialObservation,
    ) -> MetricResult:
        return self._growth_from_observations(
            name="revenue_growth",
            current=current,
            previous=previous,
            expected_metric="revenue",
        )

    def ebitda_growth(
        self,
        current: FinancialObservation,
        previous: FinancialObservation,
    ) -> MetricResult:
        return self._growth_from_observations(
            name="ebitda_growth",
            current=current,
            previous=previous,
            expected_metric="ebitda",
        )

    def pat_growth(
        self,
        current: FinancialObservation,
        previous: FinancialObservation,
    ) -> MetricResult:
        return self._growth_from_observations(
            name="pat_growth",
            current=current,
            previous=previous,
            expected_metric="pat",
        )

    def eps_growth(
        self,
        current: FinancialObservation,
        previous: FinancialObservation,
    ) -> MetricResult:
        return self._growth_from_observations(
            name="eps_growth",
            current=current,
            previous=previous,
            expected_metric="eps",
        )

    def ttm_growth(
        self,
        current: FinancialObservation,
        previous: FinancialObservation,
    ) -> MetricResult:
        name = "ttm_growth"
        invalid = _validate_observation_pair(name, current, previous)
        if invalid is not None:
            return invalid
        if current.period.kind is not PeriodKind.TTM or previous.period.kind is not PeriodKind.TTM:
            return _invalid_result(name, "percent", current.period)
        if (
            current.period.end_date is None
            or previous.period.end_date is None
            or current.period.end_date <= previous.period.end_date
        ):
            return _invalid_result(name, "percent", current.period)
        return _growth_from_values(name, current, previous)

    def quarterly_sequential_growth(
        self,
        current: FinancialObservation,
        previous: FinancialObservation,
    ) -> MetricResult:
        name = f"{current.metric}_quarterly_sequential_growth"
        invalid = _validate_observation_pair(name, current, previous)
        if invalid is not None:
            return invalid
        if current.period.kind is not PeriodKind.QUARTERLY or previous.period.kind is not PeriodKind.QUARTERLY:
            return _invalid_result(name, "percent", current.period)
        if _quarter_index(current.period) - _quarter_index(previous.period) != 1:
            return _invalid_result(name, "percent", current.period)
        return _growth_from_values(name, current, previous)

    def three_year_cagr(
        self,
        current: FinancialObservation,
        previous: FinancialObservation,
    ) -> MetricResult:
        name = f"{current.metric}_cagr_3y"
        invalid = _validate_observation_pair(name, current, previous)
        if invalid is not None:
            return invalid
        if current.period.kind is not PeriodKind.ANNUAL or previous.period.kind is not PeriodKind.ANNUAL:
            return _invalid_result(name, "percent", current.period)
        if current.period.fiscal_year - previous.period.fiscal_year != 3:
            return _invalid_result(name, "percent", current.period)
        return calculate_cagr(
            current=current.value,
            beginning=previous.value,
            years=3,
            name=name,
            period=current.period,
        )

    def _growth_from_observations(
        self,
        *,
        name: str,
        current: FinancialObservation,
        previous: FinancialObservation,
        expected_metric: str,
    ) -> MetricResult:
        invalid = _validate_observation_pair(name, current, previous)
        if invalid is not None:
            return invalid
        if current.metric != expected_metric:
            return _invalid_result(name, "percent", current.period)
        return _growth_from_values(name, current, previous)


def calculate_growth(
    current: Numeric | None,
    previous: Numeric | None,
    *,
    name: str,
    period: Period,
) -> MetricResult:
    """Calculate period-over-period growth using a positive prior base only."""

    if current is None or previous is None:
        return _missing_result(name, "percent", period)
    try:
        current_value = _to_decimal(current)
        previous_value = _to_decimal(previous)
    except (TypeError, ValueError):
        return _invalid_result(name, "percent", period)
    if previous_value <= 0:
        return _undefined_result(name, "percent", period)
    return _available_result(name, (current_value / previous_value - Decimal("1")) * Decimal("100"), "percent", period)


def calculate_cagr(
    current: Numeric | None,
    beginning: Numeric | None,
    years: int,
    *,
    name: str,
    period: Period,
) -> MetricResult:
    """Calculate CAGR only where its root has an unambiguous real result."""

    if current is None or beginning is None:
        return _missing_result(name, "percent", period)
    if years <= 0:
        return _invalid_result(name, "percent", period)
    try:
        current_value = _to_decimal(current)
        beginning_value = _to_decimal(beginning)
    except (TypeError, ValueError):
        return _invalid_result(name, "percent", period)
    if beginning_value <= 0 or current_value < 0:
        return _undefined_result(name, "percent", period)
    ratio = current_value / beginning_value
    growth = (ratio ** (Decimal("1") / Decimal(years)) - Decimal("1")) * Decimal("100")
    return _available_result(name, growth, "percent", period)


def calculate_margin(
    numerator: Numeric | None,
    revenue: Numeric | None,
    *,
    name: str,
    period: Period,
) -> MetricResult:
    if numerator is None or revenue is None:
        return _missing_result(name, "percent", period)
    try:
        numerator_value = _to_decimal(numerator)
        revenue_value = _to_decimal(revenue)
    except (TypeError, ValueError):
        return _invalid_result(name, "percent", period)
    if revenue_value == 0:
        return _undefined_result(name, "percent", period)
    return _available_result(
        name,
        numerator_value / revenue_value * Decimal("100"),
        "percent",
        period,
    )


def calculate_ratio(
    numerator: Numeric | None,
    denominator: Numeric | None,
    *,
    name: str,
    period: Period,
    unit: str = "ratio",
) -> MetricResult:
    if numerator is None or denominator is None:
        return _missing_result(name, unit, period)
    try:
        numerator_value = _to_decimal(numerator)
        denominator_value = _to_decimal(denominator)
    except (TypeError, ValueError):
        return _invalid_result(name, unit, period)
    if denominator_value == 0:
        return _undefined_result(name, unit, period)
    return _available_result(name, numerator_value / denominator_value, unit, period)


def calculate_average_balance(
    opening: Numeric | None,
    closing: Numeric | None,
    *,
    name: str,
    period: Period,
    unit: str = "currency",
) -> MetricResult:
    if opening is None or closing is None:
        return _missing_result(name, unit, period)
    try:
        opening_value = _to_decimal(opening)
        closing_value = _to_decimal(closing)
    except (TypeError, ValueError):
        return _invalid_result(name, unit, period)
    return _available_result(name, (opening_value + closing_value) / Decimal("2"), unit, period)


def _validate_observation_pair(
    name: str,
    current: FinancialObservation,
    previous: FinancialObservation,
) -> MetricResult | None:
    if (
        current.stock != previous.stock
        or current.metric != previous.metric
        or current.period.kind is not previous.period.kind
    ):
        return _invalid_result(name, "percent", current.period)
    if current.status is not ObservationStatus.AVAILABLE:
        return _status_result(name, "percent", current.period, current.status)
    if previous.status is not ObservationStatus.AVAILABLE:
        return _status_result(name, "percent", current.period, previous.status)
    return None


def _growth_from_values(
    name: str,
    current: FinancialObservation,
    previous: FinancialObservation,
) -> MetricResult:
    return calculate_growth(
        current=current.value,
        previous=previous.value,
        name=name,
        period=current.period,
    )


def _quarter_index(period: Period) -> int:
    return period.fiscal_year * 4 + period.quarter


def _available_result(name: str, value: Decimal, unit: str, period: Period) -> MetricResult:
    return MetricResult(name=name, value=value, unit=unit, period=period, status=MetricStatus.AVAILABLE)


def _missing_result(name: str, unit: str, period: Period) -> MetricResult:
    return MetricResult(name=name, value=None, unit=unit, period=period, status=MetricStatus.MISSING)


def _undefined_result(name: str, unit: str, period: Period) -> MetricResult:
    return MetricResult(name=name, value=None, unit=unit, period=period, status=MetricStatus.UNDEFINED)


def _invalid_result(name: str, unit: str, period: Period) -> MetricResult:
    return MetricResult(name=name, value=None, unit=unit, period=period, status=MetricStatus.INVALID)


def _status_result(
    name: str,
    unit: str,
    period: Period,
    status: ObservationStatus,
) -> MetricResult:
    return MetricResult(name=name, value=None, unit=unit, period=period, status=MetricStatus(status.value))


def _to_decimal(value: Numeric) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (Decimal, Real)):
        raise TypeError("value must be numeric")
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError("value cannot be represented as Decimal") from error
    if not decimal_value.is_finite():
        raise ValueError("value must be finite")
    return decimal_value
