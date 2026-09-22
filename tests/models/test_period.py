from datetime import date

import pytest

from fundamental_analysis.models.period import Period, PeriodKind


def test_period_factories_represent_all_supported_frequencies() -> None:
    annual = Period.annual(2025, end_date=date(2025, 3, 31))
    quarterly = Period.quarterly(2025, 4, end_date=date(2025, 3, 31))
    ttm = Period.ttm(end_date=date(2025, 3, 31))
    daily = Period.daily(date(2026, 9, 21))

    assert annual.kind is PeriodKind.ANNUAL
    assert quarterly.kind is PeriodKind.QUARTERLY
    assert ttm.kind is PeriodKind.TTM
    assert daily.kind is PeriodKind.DAILY


def test_same_date_has_distinct_financial_period_semantics() -> None:
    report_date = date(2025, 3, 31)
    annual = Period.annual(2025, end_date=report_date)
    quarterly = Period.quarterly(2025, 4, end_date=report_date)
    ttm = Period.ttm(end_date=report_date)

    assert annual != quarterly
    assert quarterly != ttm
    assert annual.end_date == quarterly.end_date == ttm.end_date


def test_equal_periods_compare_equal() -> None:
    assert Period.quarterly(2025, 1) == Period.quarterly(2025, 1)


@pytest.mark.parametrize(
    ("kind", "fiscal_year", "quarter", "end_date", "error"),
    [
        (PeriodKind.ANNUAL, None, None, None, "fiscal_year"),
        (PeriodKind.ANNUAL, 2025, 1, None, "annual"),
        (PeriodKind.QUARTERLY, 2025, 5, None, "quarter"),
        (PeriodKind.TTM, 2025, None, None, "TTM"),
        (PeriodKind.DAILY, None, None, None, "observation date"),
        (PeriodKind.DAILY, 2025, None, date(2025, 3, 31), "daily"),
    ],
)
def test_period_rejects_invalid_period_combinations(
    kind: PeriodKind,
    fiscal_year: int | None,
    quarter: int | None,
    end_date: date | None,
    error: str,
) -> None:
    with pytest.raises(ValueError, match=error):
        Period(kind=kind, fiscal_year=fiscal_year, quarter=quarter, end_date=end_date)
