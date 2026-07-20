"""Application services and use-case orchestration."""

from prismops.services.support_analytics import (
    analyze_support_tickets,
    calculate_automation_score,
)
from prismops.services.support_audit import run_support_audit
from prismops.services.support_opportunities import (
    explain_automation_opportunity,
    rank_automation_opportunities,
)

__all__ = [
    "analyze_support_tickets",
    "calculate_automation_score",
    "explain_automation_opportunity",
    "rank_automation_opportunities",
    "run_support_audit",
]
