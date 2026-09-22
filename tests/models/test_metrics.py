from decimal import Decimal

import pytest

from fundamental_analysis.models.metrics import MetricResult, MetricStatus
from fundamental_analysis.models.period import Period


def test_metric_result_can_represent_an_available_calculation() -> None:
    result = MetricResult(
        name="ebitda_margin",
        value=Decimal("20.0"),
        unit="percent",
        period=Period.annual(2025),
        status=MetricStatus.AVAILABLE,
    )

    assert result.value == Decimal("20.0")
    assert result.unit == "percent"


def test_metric_result_can_represent_an_unavailable_calculation() -> None:
    result = MetricResult(
        name="roe",
        value=None,
        unit="percent",
        period=Period.annual(2025),
        status=MetricStatus.MISSING,
    )

    assert result.value is None
    assert result.status is MetricStatus.MISSING


@pytest.mark.parametrize(
    "field,value",
    [("name", ""), ("unit", " "), ("period", "FY2025"), ("status", "available")],
)
def test_metric_result_rejects_blank_required_text(field: str, value: str) -> None:
    values = {
        "name": "roe",
        "value": Decimal("18.4"),
        "unit": "percent",
        "period": Period.annual(2025),
        "status": MetricStatus.AVAILABLE,
    }
    values[field] = value

    error_type = TypeError if field in {"period", "status"} else ValueError
    with pytest.raises(error_type, match=field):
        MetricResult(**values)


def test_metric_result_rejects_a_value_for_an_unavailable_status() -> None:
    with pytest.raises(ValueError, match="unavailable metrics"):
        MetricResult(
            name="roe",
            value=Decimal("18.4"),
            unit="percent",
            period=Period.annual(2025),
            status=MetricStatus.MISSING,
        )
