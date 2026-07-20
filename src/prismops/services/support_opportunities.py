"""Deterministic ranking and explanations for support automation opportunities."""

from __future__ import annotations

from collections.abc import Sequence

from prismops.models.support import AutomationOpportunity, CategoryMetrics
from prismops.services.support_analytics import PROCESS_FACTORS


def explain_automation_opportunity(
    metrics: CategoryMetrics, *, maximum_category_count: int
) -> str:
    """Explain a category score using only its metrics and documented factors."""

    factors = PROCESS_FACTORS[metrics.category.value]
    volume_ratio = (
        metrics.ticket_count / maximum_category_count if maximum_category_count else 0
    )
    reasons: list[str] = []

    if volume_ratio >= 0.75:
        reasons.append("High volume increases the potential impact")
    elif volume_ratio >= 0.35:
        reasons.append("Moderate volume creates a meaningful opportunity")
    else:
        reasons.append("Lower volume limits the potential impact")

    if factors["repetitiveness"] >= 0.8:
        reasons.append("the workflow is highly repetitive")
    elif factors["repetitiveness"] < 0.4:
        reasons.append("limited repetition reduces suitability")

    if metrics.average_resolution_minutes >= 60:
        reasons.append(
            "long handling time increases potential savings but does not guarantee suitability"
        )

    if metrics.escalation_rate >= 0.30:
        reasons.append("a high escalation rate reduces the score")
    elif metrics.escalation_rate <= 0.08:
        reasons.append("a low escalation rate supports automation suitability")

    if factors["process_consistency"] < 0.5:
        reasons.append("an inconsistent process reduces the score")
    elif factors["process_consistency"] >= 0.8:
        reasons.append("a consistent process supports repeatable automation")

    return "; ".join(reasons) + "."


def rank_automation_opportunities(
    categories: Sequence[CategoryMetrics],
) -> list[AutomationOpportunity]:
    """Rank category metrics by score with stable alphabetical tie-breaking."""

    if not categories:
        return []
    ordered = sorted(
        categories,
        key=lambda item: (-item.automation_score, item.category.value),
    )
    maximum_count = max(item.ticket_count for item in categories)
    return [
        AutomationOpportunity(
            rank=index,
            metrics=metrics,
            explanation=explain_automation_opportunity(
                metrics, maximum_category_count=maximum_count
            ),
        )
        for index, metrics in enumerate(ordered, start=1)
    ]
