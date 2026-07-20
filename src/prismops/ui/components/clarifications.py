"""Streamlit components for optional stakeholder clarification and refinement."""

from __future__ import annotations

from collections.abc import Mapping

import streamlit as st

from prismops.models.ai_audit import ClarificationQuestionBatch


def render_clarification_form(
    questions: ClarificationQuestionBatch,
    existing_answers: Mapping[str, str],
) -> tuple[bool, dict[str, str]]:
    st.markdown("#### Optional clarification")
    st.caption(
        "These targeted questions identify missing operational context. Answers remain "
        "stakeholder-provided context and cannot change verified metrics."
    )
    if not questions.questions:
        st.info("The initial report did not identify any material clarification questions.")
        return False, {}

    answers: dict[str, str] = {}
    with st.form("clarification_form"):
        for item in questions.questions:
            st.markdown(f"**{item.question}**")
            st.caption(f"Why it matters: {item.rationale}")
            answers[item.question_id] = st.text_area(
                "Optional answer",
                value=existing_answers.get(item.question_id, ""),
                key=f"clarification_answer_{item.question_id}",
                label_visibility="collapsed",
            )
        submitted = st.form_submit_button("Refine Recommendations", type="primary")
    return submitted, answers
