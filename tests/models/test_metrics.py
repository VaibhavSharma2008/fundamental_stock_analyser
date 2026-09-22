from decimal import Decimal

import pytest

from fundamental_analysis.models.metrics import MetricResult
from fundamental_analysis.models.period import Period


def test_metric_result_can_represent_an_available_calculation() -> None:
    result = MetricResult(
        name="ebitda_margin",
        value=Decimal("20.0"),
        unit="percent",
        period=Period.annual(2025),
        status="available",
    )

    assert result.value == Decimal("20.0")
    assert result.unit == "percent"


def test_metric_result_can_represent_an_unavailable_calculation() -> None:
    result = MetricResult(
        name="roe",
        value=None,
        unit="percent",
        period=Period.annual(2025),
        status="missing",
    )

    assert result.value is None
    assert result.status == "missing"


@pytest.mark.parametrize("field,value", [("name", ""), ("unit", " "), ("period", "FY2025"), ("status", "")])
def test_metric_result_rejects_blank_required_text(field: str, value: str) -> None:
    values = {
        "name": "roe",
        "value": Decimal("18.4"),
        "unit": "percent",
        "period": Period.annual(2025),
        "status": "available",
    }
    values[field] = value

    error_type = TypeError if field == "period" else ValueError
    with pytest.raises(error_type, match=field):
        MetricResult(**values)
