"""Tests for deterministic automation rankings and explanations."""

from prismops.models.support import CategoryMetrics, TicketCategory
from prismops.services.support_opportunities import (
    explain_automation_opportunity,
    rank_automation_opportunities,
)


def test_category_ranking_uses_score_then_category_name() -> None:
    categories = [
        _metrics(TicketCategory.RETURN_REQUEST, score=60, count=40),
        _metrics(TicketCategory.BILLING_QUESTION, score=60, count=50),
        _metrics(TicketCategory.ORDER_STATUS, score=90, count=100),
    ]

    ranked = rank_automation_opportunities(categories)

    assert [item.metrics.category for item in ranked] == [
        TicketCategory.ORDER_STATUS,
        TicketCategory.BILLING_QUESTION,
        TicketCategory.RETURN_REQUEST,
    ]
    assert [item.rank for item in ranked] == [1, 2, 3]


def test_explanation_reflects_positive_and_negative_factors() -> None:
    order_status = _metrics(
        TicketCategory.ORDER_STATUS, score=90, count=100, minutes=12, escalation=0.03
    )
    damaged = _metrics(
        TicketCategory.DAMAGED_SHIPMENT,
        score=40,
        count=20,
        minutes=120,
        escalation=0.50,
    )

    positive = explain_automation_opportunity(
        order_status, maximum_category_count=100
    )
    negative = explain_automation_opportunity(damaged, maximum_category_count=100)

    assert "High volume" in positive
    assert "highly repetitive" in positive
    assert "low escalation rate" in positive
    assert "Lower volume" in negative
    assert "long handling time" in negative
    assert "high escalation rate reduces" in negative
    assert "inconsistent process" in negative


def _metrics(
    category: TicketCategory,
    *,
    score: float,
    count: int,
    minutes: float = 30,
    escalation: float = 0.10,
) -> CategoryMetrics:
    return CategoryMetrics(
        category=category,
        ticket_count=count,
        category_percentage=50,
        average_resolution_minutes=minutes,
        total_handling_hours=20,
        escalation_rate=escalation,
        automation_score=score,
    )
