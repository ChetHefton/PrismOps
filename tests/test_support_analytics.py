"""Tests for deterministic support analytics and embedded patterns."""

import pandas as pd
import pytest

from prismops.data.demo import load_support_tickets
from prismops.services.support_analytics import analyze_support_tickets


def test_aggregate_calculations_are_correct() -> None:
    tickets = pd.DataFrame(
        [
            _ticket("1", "order status", 10, False, "email", "standard"),
            _ticket("2", "order status", 20, False, "email", "priority"),
            _ticket("3", "damaged shipment", 30, True, "phone", "standard"),
            _ticket("4", "damaged shipment", 60, True, "phone", "standard"),
        ]
    )

    summary = analyze_support_tickets(tickets)
    categories = {metric.category.value: metric for metric in summary.by_category}

    assert summary.total_ticket_count == 4
    assert summary.total_handling_hours == pytest.approx(2.0)
    assert summary.overall_escalation_rate == pytest.approx(0.5)
    assert categories["order status"].ticket_count == 2
    assert categories["order status"].category_percentage == pytest.approx(50.0)
    assert categories["order status"].average_resolution_minutes == pytest.approx(15.0)
    assert categories["order status"].total_handling_hours == pytest.approx(0.5)
    assert categories["order status"].escalation_rate == pytest.approx(0.0)
    assert sum(item.ticket_count for item in summary.by_channel) == 4
    assert sum(item.ticket_count for item in summary.by_customer_tier) == 4


def test_demo_percentages_scores_and_known_patterns() -> None:
    summary = analyze_support_tickets(load_support_tickets())
    categories = {metric.category.value: metric for metric in summary.by_category}

    assert sum(metric.category_percentage for metric in summary.by_category) == pytest.approx(
        100.0
    )
    assert all(0 <= metric.automation_score <= 100 for metric in summary.by_category)
    assert categories["order status"].ticket_count > categories["damaged shipment"].ticket_count
    assert (
        categories["order status"].average_resolution_minutes
        < categories["billing question"].average_resolution_minutes
    )
    assert (
        categories["damaged shipment"].escalation_rate
        > categories["billing question"].escalation_rate
    )
    assert (
        categories["account access"].average_resolution_minutes
        < categories["product question"].average_resolution_minutes
    )
    assert (
        categories["order status"].automation_score
        > categories["miscellaneous"].automation_score
    )


def _ticket(
    ticket_id: str,
    category: str,
    minutes: int,
    escalated: bool,
    channel: str,
    tier: str,
) -> dict[str, object]:
    return {
        "ticket_id": ticket_id,
        "created_at": pd.Timestamp("2025-01-01", tz="UTC"),
        "category": category,
        "description": "Test ticket",
        "resolution_minutes": minutes,
        "escalated": escalated,
        "channel": channel,
        "customer_tier": tier,
    }
