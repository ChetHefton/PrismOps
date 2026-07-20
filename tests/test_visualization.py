"""Tests for Plotly support chart builders."""

import pytest

from prismops.models.support import CategoryMetrics, TicketCategory
from prismops.visualization import (
    build_automation_score_chart,
    build_handling_hours_chart,
    build_ticket_volume_chart,
)


@pytest.fixture
def categories() -> list[CategoryMetrics]:
    return [
        CategoryMetrics(
            category=TicketCategory.BILLING_QUESTION,
            ticket_count=20,
            category_percentage=25,
            average_resolution_minutes=50,
            total_handling_hours=16.67,
            escalation_rate=0.2,
            automation_score=60,
        ),
        CategoryMetrics(
            category=TicketCategory.ORDER_STATUS,
            ticket_count=60,
            category_percentage=75,
            average_resolution_minutes=10,
            total_handling_hours=10,
            escalation_rate=0.02,
            automation_score=85,
        ),
    ]


def test_chart_builders_order_their_inputs(categories: list[CategoryMetrics]) -> None:
    volume = build_ticket_volume_chart(categories)
    handling = build_handling_hours_chart(categories)
    automation = build_automation_score_chart(categories)

    assert list(volume.data[0].y) == ["Order Status", "Billing Question"]
    assert list(volume.data[0].x) == [60, 20]
    assert list(handling.data[0].y) == ["Billing Question", "Order Status"]
    assert list(automation.data[0].x) == [85, 60]
    assert list(automation.layout.xaxis.range) == [0, 108]
    assert volume.data[0].orientation == "h"
    assert volume.layout.paper_bgcolor == "rgba(0,0,0,0)"
    assert volume.layout.plot_bgcolor == "rgba(0,0,0,0)"


@pytest.mark.parametrize(
    "builder",
    [build_ticket_volume_chart, build_handling_hours_chart, build_automation_score_chart],
)
def test_chart_builders_reject_empty_input(builder) -> None:
    with pytest.raises(ValueError, match="At least one category"):
        builder([])
