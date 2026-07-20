"""Reusable Streamlit presentation components for a completed support audit."""

from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from prismops.models.support import SupportAudit
from prismops.visualization import (
    build_automation_score_chart,
    build_handling_hours_chart,
    build_ticket_volume_chart,
)


def render_executive_overview(audit: SupportAudit) -> None:
    _section_heading("Executive overview", "AUDIT SNAPSHOT", "executive-overview")
    highest_volume = max(audit.summary.by_category, key=lambda item: item.ticket_count)
    top_automation = max(
        audit.summary.by_category, key=lambda item: item.automation_score
    )
    cards = (
        (
            "Total tickets",
            f"{audit.summary.total_ticket_count:,}",
            "Across Jan–Jun 2025",
            "#9b7cff",
        ),
        (
            "Handling hours",
            f"{audit.summary.total_handling_hours:,.1f}",
            "Recorded resolution effort",
            "#36d7e7",
        ),
        (
            "Escalation rate",
            f"{audit.summary.overall_escalation_rate:.1%}",
            "Share requiring escalation",
            "#f6bd60",
        ),
        (
            "Highest-volume category",
            highest_volume.category.value.title(),
            f"{highest_volume.ticket_count:,} tickets",
            "#4f8cff",
        ),
        (
            "Top automation opportunity",
            top_automation.category.value.title(),
            f"{top_automation.automation_score:.1f} out of 100",
            "#3dd6a0",
        ),
    )
    html = '<div class="prismops-metric-grid">'
    for label, value, support, accent in cards:
        html += f"""
        <div class="prismops-metric-card" style="--metric-accent:{accent}">
          <div class="prismops-metric-label">{escape(label)}</div>
          <div class="prismops-metric-value">{escape(value)}</div>
          <div class="prismops-metric-support">{escape(support)}</div>
        </div>"""
    st.markdown(html + "</div>", unsafe_allow_html=True)


def render_category_analysis(audit: SupportAudit) -> None:
    _section_heading(
        "Detailed category table", "VERIFIED METRICS", "category-details"
    )
    st.caption("Sort any column to compare operational performance and score inputs.")
    frame = pd.DataFrame(
        {
            "Category": item.category.value.title(),
            "Ticket count": item.ticket_count,
            "Category percentage": item.category_percentage,
            "Average resolution minutes": item.average_resolution_minutes,
            "Total handling hours": item.total_handling_hours,
            "Escalation rate": item.escalation_rate * 100,
            "Automation score": item.automation_score,
        }
        for item in audit.summary.by_category
    )
    st.dataframe(
        frame,
        hide_index=True,
        width="stretch",
        column_config={
            "Ticket count": st.column_config.NumberColumn(format=",d"),
            "Category percentage": st.column_config.NumberColumn(format="%.1f%%"),
            "Average resolution minutes": st.column_config.NumberColumn(format="%.1f"),
            "Total handling hours": st.column_config.NumberColumn(format="%.1f"),
            "Escalation rate": st.column_config.NumberColumn(format="%.1f%%"),
            "Automation score": st.column_config.NumberColumn(format="%.1f"),
        },
    )


def render_visualizations(audit: SupportAudit) -> None:
    _section_heading(
        "Category visualizations", "OPERATIONAL PROFILE", "analytics"
    )
    st.caption(
        "Compare demand, effort, and deterministic opportunity scores across support categories."
    )
    columns = st.columns(3, gap="medium")
    figures = (
        build_ticket_volume_chart(audit.summary.by_category),
        build_handling_hours_chart(audit.summary.by_category),
        build_automation_score_chart(audit.summary.by_category),
    )
    for column, figure in zip(columns, figures, strict=True):
        column.plotly_chart(
            figure,
            width="stretch",
            config={"displayModeBar": False, "responsive": True},
        )


def render_opportunity_ranking(audit: SupportAudit) -> None:
    _section_heading(
        "Automation opportunity ranking", "DETERMINISTIC PRIORITY", "opportunities"
    )
    st.caption(
        "Prioritized using deterministic scoring; final implementation decisions require operational review."
    )
    for opportunity in audit.opportunities[:3]:
        st.markdown(_ranking_card(opportunity), unsafe_allow_html=True)

    remaining = audit.opportunities[3:]
    if remaining:
        with st.expander(f"View {len(remaining)} additional ranked categories"):
            for opportunity in remaining:
                st.markdown(_ranking_card(opportunity), unsafe_allow_html=True)


def render_process_documentation(audit: SupportAudit) -> None:
    _section_heading(
        "Process documentation", "SUPPLIED OPERATIONAL CONTEXT", "process-documentation"
    )
    with st.expander("Inspect documented workflows, systems, and exception paths"):
        st.markdown(audit.process_documentation)


def render_scoring_methodology() -> None:
    _section_heading(
        "Scoring methodology", "TRANSPARENT RULES", "scoring-methodology"
    )
    with st.expander("How the automation score works"):
        st.markdown(
            """
The preliminary score is calculated from explicit rules:

- **30% — Volume:** category tickets divided by the highest category volume
- **25% — Repetitiveness:** documented category factor from 0 to 1
- **15% — Handling-time opportunity:** average resolution minutes divided by 90, capped at 1
- **15% — Escalation suitability:** 1 minus the category escalation rate
- **15% — Process consistency:** documented category factor from 0 to 1

The weighted result is multiplied by 100 and bounded from 0 to 100. The score is deterministic and preliminary. It is not a prediction, a guarantee of feasibility, or a substitute for operational review.
"""
        )


def _ranking_card(opportunity) -> str:
    metrics = opportunity.metrics
    score = metrics.automation_score
    if score >= 75:
        band, band_color = "Strong opportunity", "#3dd6a0"
    elif score >= 55:
        band, band_color = "Moderate opportunity", "#f6bd60"
    else:
        band, band_color = "Limited opportunity", "#ff7b72"
    rationale = opportunity.explanation.removesuffix(".")
    return f"""
    <div class="prismops-rank-card">
      <div class="prismops-rank-head">
        <span class="prismops-rank-badge">#{opportunity.rank}</span>
        <span class="prismops-rank-name">{escape(metrics.category.value.title())}</span>
        <span class="prismops-score-badge" style="border-color:{band_color};color:{band_color}">{score:.1f} / 100 · {band}</span>
      </div>
      <div class="prismops-rank-meta">Volume {metrics.ticket_count:,} &nbsp;·&nbsp; Avg. resolution {metrics.average_resolution_minutes:.1f} min &nbsp;·&nbsp; Escalation {metrics.escalation_rate:.1%}</div>
      <div class="prismops-rank-reason">{escape(rationale)}.</div>
      <div class="prismops-progress" role="progressbar" aria-label="Automation score" aria-valuenow="{score:.1f}" aria-valuemin="0" aria-valuemax="100"><span style="width:{score:.1f}%"></span></div>
    </div>"""


def _section_heading(title: str, kicker: str, anchor: str) -> None:
    st.markdown(
        f'<div id="{anchor}" class="prismops-section-anchor"><div class="prismops-section-kicker">{escape(kicker)}</div></div>',
        unsafe_allow_html=True,
    )
    st.subheader(title)
