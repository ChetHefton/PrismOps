"""Application facade for running the complete preloaded support audit."""

from __future__ import annotations

from pathlib import Path

from prismops.data.demo import (
    load_demo_company,
    load_support_process,
    load_support_tickets,
)
from prismops.data.companies import DEFAULT_COMPANY_ID, get_demo_company_config
from prismops.models.support import SupportAudit
from prismops.services.support_analytics import analyze_support_tickets
from prismops.services.support_opportunities import rank_automation_opportunities


def run_support_audit(
    *,
    company_id: str = DEFAULT_COMPANY_ID,
    company_path: Path | None = None,
    tickets_path: Path | None = None,
    process_path: Path | None = None,
) -> SupportAudit:
    """Load, validate, and analyze all inputs required by the dashboard."""

    config = get_demo_company_config(company_id)
    company = load_demo_company(company_path or config.company_path)
    tickets = load_support_tickets(tickets_path or config.tickets_path)
    process_documentation = load_support_process(process_path or config.process_path)
    summary = analyze_support_tickets(tickets)
    opportunities = rank_automation_opportunities(summary.by_category)
    highest_volume = max(
        summary.by_category,
        key=lambda item: (item.ticket_count, item.category.value),
    )

    return SupportAudit(
        company=company,
        summary=summary,
        opportunities=opportunities,
        process_documentation=process_documentation,
        highest_volume_category=highest_volume.category,
        highest_automation_category=opportunities[0].metrics.category,
    )
