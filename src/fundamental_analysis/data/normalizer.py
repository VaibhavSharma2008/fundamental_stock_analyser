"""Provider-field and sign normalization for financial facts."""

from dataclasses import replace
from decimal import Decimal
from numbers import Real

from fundamental_analysis.models.financials import FinancialObservation, ObservationStatus


STANDARD_FINANCIAL_FIELDS = frozenset(
    {
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
        "current_assets",
        "current_liabilities",
        "cogs",
        "book_value_per_share",
    }
)

_ALIASES_BY_FIELD = {
    "revenue": {"revenue", "totalRevenue", "sales"},
    "ebitda": {"ebitda"},
    "ebit": {"ebit", "operatingProfit"},
    "pat": {"pat", "netProfit", "profitAfterTax"},
    "eps": {"eps", "earningsPerShare"},
    "equity": {"equity", "shareholdersEquity", "totalEquity"},
    "debt": {"debt", "totalDebt", "grossDebt"},
    "cash": {"cash", "cashAndEquivalents", "cashEquivalents"},
    "receivables": {"receivables", "tradeReceivables", "accountsReceivable"},
    "inventory": {"inventory", "inventories"},
    "payables": {"payables", "tradePayables", "accountsPayable"},
    "cfo": {"cfo", "operatingCashFlow", "cashFromOperations"},
    "capex": {"capex", "capitalExpenditure", "capitalExpenditures"},
    "interest_expense": {"interestExpense", "financeCost", "interest"},
    "shares_outstanding": {"sharesOutstanding", "shares"},
    "current_assets": {"currentAssets"},
    "current_liabilities": {"currentLiabilities"},
    "cogs": {"cogs", "costOfGoodsSold"},
    "book_value_per_share": {"bookValuePerShare", "bvps"},
}


def _field_key(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


FINANCIAL_FIELD_ALIASES = {
    _field_key(alias): canonical
    for canonical, aliases in _ALIASES_BY_FIELD.items()
    for alias in aliases
}

_POSITIVE_OUTFLOW_FIELDS = frozenset({"capex", "interest_expense"})

SIGN_CONVENTIONS = {
    "capex": "positive cash outflow",
    "interest_expense": "positive expense",
    "cfo": "positive cash inflow; negative cash burn is preserved",
    "debt": "positive balance",
    "cash": "positive balance",
}


def normalize_financial_field(provider_field: str) -> str | None:
    """Return the canonical internal field for a provider-specific name."""

    if not isinstance(provider_field, str) or not provider_field.strip():
        return None
    return FINANCIAL_FIELD_ALIASES.get(_field_key(provider_field))


def normalize_sign(metric: str, value: Decimal | Real) -> Decimal:
    """Apply the POC's explicit sign convention to a normalized fact."""

    decimal_value = _to_decimal(value)
    if metric in _POSITIVE_OUTFLOW_FIELDS:
        return abs(decimal_value)
    return decimal_value


def normalize_missing_status(
    value: Decimal | Real | None,
    status: ObservationStatus = ObservationStatus.AVAILABLE,
) -> ObservationStatus:
    """Make a missing value explicit without treating it as zero."""

    if value is None and status is ObservationStatus.AVAILABLE:
        return ObservationStatus.MISSING
    return status


def normalize_financial_observation(observation: FinancialObservation) -> FinancialObservation:
    """Return a standardized observation suitable for metric calculations."""

    metric = normalize_financial_field(observation.metric)
    if metric is None:
        raise ValueError(f"unknown provider field: {observation.metric}")

    status = normalize_missing_status(observation.value, observation.status)
    value = None if observation.value is None else normalize_sign(metric, observation.value)
    return replace(observation, metric=metric, value=value, status=status)


def _to_decimal(value: Decimal | Real) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (Decimal, Real)):
        raise TypeError("value must be numeric")
    decimal_value = Decimal(str(value))
    if not decimal_value.is_finite():
        raise ValueError("value must be finite")
    return decimal_value
