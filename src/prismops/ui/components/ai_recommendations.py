"""Compact Streamlit rendering for verified AI-generated recommendations."""

from __future__ import annotations

from html import escape

import streamlit as st

from prismops.models.ai_audit import ExecutiveAuditReport


def render_ai_report(report: ExecutiveAuditReport) -> None:
    """Render verified report fields in compact, accessible cards."""

    st.markdown(
        f'<div class="prismops-summary-card"><strong>Executive summary</strong><p>{escape(report.executive_summary)}</p></div>',
        unsafe_allow_html=True,
    )
    for recommendation in report.recommendations:
        details = (
            ("Current workflow", [recommendation.current_workflow], "#4f8cff"),
            ("Exact evidence", recommendation.evidence, "#36d7e7"),
            ("Expected benefits", recommendation.expected_benefits, "#3dd6a0"),
            ("Assumptions", recommendation.assumptions, "#f6bd60"),
            ("Risks", recommendation.risks, "#ff7b72"),
            ("Human review", recommendation.human_review_points, "#ec67d6"),
        )
        detail_html = '<div class="prismops-detail-grid">'
        for title, values, color in details:
            items = "".join(f"<li>{escape(value)}</li>" for value in values)
            detail_html += f'<div class="prismops-detail" style="--detail-accent:{color}"><strong>{title}</strong><ul>{items}</ul></div>'
        detail_html += "</div>"
        st.markdown(
            f"""
            <article class="prismops-report-card">
              <div class="prismops-report-head">
                <div><h4>{escape(recommendation.title)}</h4><span class="prismops-rank-reason">{escape(recommendation.category.title())}</span></div>
                <span class="prismops-confidence">{escape(recommendation.confidence.title())} confidence</span>
              </div>
              <p><strong>Proposed automation</strong><br>{escape(recommendation.proposed_automation)}</p>
              {detail_html}
            </article>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("AI report limitations"):
        for limitation in report.limitations:
            st.markdown(f"- {limitation}")
