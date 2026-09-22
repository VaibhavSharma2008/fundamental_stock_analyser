"""Period semantics for financial, ownership, and market observations."""

from dataclasses import dataclass
from datetime import date
from enum import Enum


class PeriodKind(str, Enum):
    """The frequencies supported by the POC."""

    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    TTM = "ttm"
    DAILY = "daily"


@dataclass(frozen=True, slots=True)
class Period:
    """An explicitly typed reporting or observation period.

    ``end_date`` may be shared by different period kinds. Its meaning remains
    unambiguous because ``kind`` records whether it is an annual, quarterly,
    TTM, or daily observation.
    """

    kind: PeriodKind
    fiscal_year: int | None = None
    quarter: int | None = None
    end_date: date | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, PeriodKind):
            raise TypeError("kind must be a PeriodKind")

        if self.kind is PeriodKind.ANNUAL:
            self._validate_annual()
        elif self.kind is PeriodKind.QUARTERLY:
            self._validate_quarterly()
        elif self.kind is PeriodKind.TTM:
            self._validate_ttm()
        else:
            self._validate_daily()

    @classmethod
    def annual(cls, fiscal_year: int, end_date: date | None = None) -> "Period":
        return cls(kind=PeriodKind.ANNUAL, fiscal_year=fiscal_year, end_date=end_date)

    @classmethod
    def quarterly(
        cls,
        fiscal_year: int,
        quarter: int,
        end_date: date | None = None,
    ) -> "Period":
        return cls(
            kind=PeriodKind.QUARTERLY,
            fiscal_year=fiscal_year,
            quarter=quarter,
            end_date=end_date,
        )

    @classmethod
    def ttm(cls, end_date: date | None = None) -> "Period":
        return cls(kind=PeriodKind.TTM, end_date=end_date)

    @classmethod
    def daily(cls, observed_on: date) -> "Period":
        return cls(kind=PeriodKind.DAILY, end_date=observed_on)

    def _validate_annual(self) -> None:
        _require_fiscal_year(self.fiscal_year)
        if self.quarter is not None:
            raise ValueError("annual periods cannot specify a quarter")

    def _validate_quarterly(self) -> None:
        _require_fiscal_year(self.fiscal_year)
        if self.quarter not in {1, 2, 3, 4}:
            raise ValueError("quarter must be between 1 and 4 for quarterly periods")

    def _validate_ttm(self) -> None:
        if self.fiscal_year is not None or self.quarter is not None:
            raise ValueError("TTM periods cannot specify a fiscal year or quarter")

    def _validate_daily(self) -> None:
        if self.fiscal_year is not None or self.quarter is not None:
            raise ValueError("daily periods cannot specify a fiscal year or quarter")
        if not isinstance(self.end_date, date):
            raise ValueError("daily periods require an observation date")


def _require_fiscal_year(fiscal_year: int | None) -> None:
    if not isinstance(fiscal_year, int) or isinstance(fiscal_year, bool) or fiscal_year < 1:
        raise ValueError("fiscal_year must be a positive integer")
