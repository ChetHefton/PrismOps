"""Streamlit rendering for bounded, session-only audit conversation."""

from __future__ import annotations

import streamlit as st

from prismops.models.ai_audit import ChatTurn


def render_chat_history(history: list[ChatTurn]) -> None:
    for turn in history:
        with st.chat_message(turn.role):
            st.write(turn.content)
            if turn.role == "assistant" and turn.answer_details:
                details = turn.answer_details
                with st.expander("Evidence used"):
                    if details.evidence_used:
                        for item in details.evidence_used:
                            st.markdown(f"- {item}")
                    else:
                        st.caption("No audit evidence was required for this response.")
                if details.assumptions:
                    st.markdown("**Assumptions**")
                    for item in details.assumptions:
                        st.markdown(f"- {item}")
                if details.missing_information:
                    st.markdown("**Missing information**")
                    for item in details.missing_information:
                        st.markdown(f"- {item}")
