"""Session-state keys and narrowly scoped state mutations."""

from collections.abc import MutableMapping
from typing import Any

AUDIT_STATE_KEY = "northstar_support_audit"
AI_RESULT_STATE_KEY = "northstar_ai_grounded_result"
AI_REPORT_STATE_KEY = "northstar_ai_report"
CLARIFICATION_QUESTIONS_STATE_KEY = "northstar_clarification_questions"
CLARIFICATION_ANSWERS_STATE_KEY = "northstar_clarification_answers"
REFINED_REPORT_STATE_KEY = "northstar_refined_ai_report"
CHAT_HISTORY_STATE_KEY = "northstar_audit_chat_history"
SELECTED_COMPANY_STATE_KEY = "selected_demo_company"


def clear_conversation(state: MutableMapping[str, Any]) -> None:
    """Clear only session chat memory, preserving all audit artifacts."""

    state[CHAT_HISTORY_STATE_KEY] = []


def clear_ai_results(state: MutableMapping[str, Any]) -> None:
    """Clear AI artifacts after a new deterministic audit is explicitly run."""

    for key in (
        AI_RESULT_STATE_KEY,
        AI_REPORT_STATE_KEY,
        CLARIFICATION_QUESTIONS_STATE_KEY,
        CLARIFICATION_ANSWERS_STATE_KEY,
        REFINED_REPORT_STATE_KEY,
        CHAT_HISTORY_STATE_KEY,
    ):
        state.pop(key, None)


def clear_company_results(state: MutableMapping[str, Any]) -> None:
    """Clear all evidence-bearing state when the selected company changes."""

    state.pop(AUDIT_STATE_KEY, None)
    clear_ai_results(state)
