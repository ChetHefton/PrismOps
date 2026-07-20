"""Streamlit composition for deterministic and grounded-AI support auditing."""

from __future__ import annotations

import streamlit as st
from pydantic import ValidationError

from prismops.agents import (
    GraphValidationError,
    run_ai_support_audit_result,
)
from prismops.agents.provider import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMNetworkError,
    LLMProviderError,
    LLMQuotaError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMUnsupportedModelError,
    MalformedStructuredOutputError,
    create_structured_output_client,
)
from prismops.config import get_llm_settings, get_settings
from prismops.data.demo import DemoDataValidationError
from prismops.data.companies import DEMO_COMPANIES, get_demo_company_config
from prismops.data.demo import load_demo_company
from prismops.models.ai_audit import (
    ChatTurn,
    ClarificationQuestionBatch,
    ExecutiveAuditReport,
    GroundedAuditResult,
    StakeholderClarification,
)
from prismops.models.support import SupportAudit
from prismops.services.ai_interactions import (
    ChatGroundingError,
    ClarificationContradictionError,
    answer_audit_question,
    build_chat_context,
    refine_audit_report,
)
from prismops.services import (
    run_support_audit,
)
from prismops.ui.components import (
    render_ai_report,
    render_category_analysis,
    render_chat_history,
    render_clarification_form,
    render_executive_overview,
    render_opportunity_ranking,
    render_process_documentation,
    render_scoring_methodology,
    render_visualizations,
)
from prismops.ui.theme import apply_prismops_theme
from prismops.ui.session import (
    AI_REPORT_STATE_KEY,
    AI_RESULT_STATE_KEY,
    AUDIT_STATE_KEY,
    CHAT_HISTORY_STATE_KEY,
    CLARIFICATION_ANSWERS_STATE_KEY,
    CLARIFICATION_QUESTIONS_STATE_KEY,
    REFINED_REPORT_STATE_KEY,
    clear_ai_results,
    clear_company_results,
    clear_conversation,
    SELECTED_COMPANY_STATE_KEY,
)


def run() -> None:
    """Render the complete selected-company audit flow."""

    st.set_page_config(page_title="PrismOps", page_icon="🔷", layout="wide")
    apply_prismops_theme()
    settings, ai_enabled = _render_sidebar_status()

    st.markdown(
        """
        <header class="prismops-hero" id="audit">
          <div class="prismops-eyebrow">AI Operations Intelligence</div>
          <h1>Prism<span class="prismops-gradient-text">Ops</span></h1>
          <p>Turn verified support operations data into transparent priorities and grounded AI recommendations.</p>
        </header>
        """,
        unsafe_allow_html=True,
    )

    display_to_id = {item.display_name: item.company_id for item in DEMO_COMPANIES}
    company, action = st.columns([4, 1], vertical_alignment="bottom", gap="medium")
    with company:
        selected_display = st.selectbox(
            "Company",
            options=list(display_to_id),
            index=0,
            key=SELECTED_COMPANY_STATE_KEY,
            on_change=_handle_company_change,
        )
    selected_id = display_to_id[selected_display]
    selected_config = get_demo_company_config(selected_id)
    selected_company = load_demo_company(selected_config.company_path)
    with action:
        run_requested = st.button(
            "Run Support Audit", type="primary", width="stretch"
        )
    st.caption(
        f"{selected_company.demo_status} · {selected_company.industry} · "
        f"{selected_company.reporting_period_start:%b %Y}–{selected_company.reporting_period_end:%b %Y} · "
        f"{selected_company.ticket_count:,} tickets"
    )
    st.caption(
        "Custom business-data upload and live system integrations are under development. "
        "This release currently supports preloaded fictional demo datasets only."
    )

    if run_requested:
        _run_deterministic_audit(selected_id, selected_company.name)

    audit = st.session_state.get(AUDIT_STATE_KEY)
    if isinstance(audit, SupportAudit) and audit.company.id != selected_id:
        clear_company_results(st.session_state)
        audit = None
    if not isinstance(audit, SupportAudit):
        st.info(
            "Run the support audit to validate the preloaded demo and calculate deterministic results."
        )
        return

    st.markdown(
        f'<div class="prismops-status-success">✓ Support audit complete · {audit.summary.total_ticket_count:,} tickets analyzed</div>',
        unsafe_allow_html=True,
    )
    _render_dashboard(audit, ai_enabled=ai_enabled, max_chat_messages=settings.max_chat_messages if settings else 6)


def _render_sidebar_status():
    try:
        settings = get_settings()
        public = get_llm_settings(settings)
        enabled = public.api_key_configured
        with st.sidebar:
            st.markdown('<div class="prismops-sidebar-brand">PrismOps</div><div class="prismops-sidebar-tag">Deterministic analytics + grounded AI</div>', unsafe_allow_html=True)
            badge_class = "prismops-status-badge" if enabled else "prismops-status-badge off"
            badge_text = "Enabled" if enabled else "Setup required"
            st.markdown(f'<span class="{badge_class}">AI · {badge_text}</span>', unsafe_allow_html=True)
            if enabled:
                st.caption(f"Model · {public.model}")
            else:
                st.caption("Add your local key to enable AI features.")
            st.markdown(
                """
                <nav class="prismops-nav" aria-label="Dashboard sections">
                  <a href="#audit">Audit</a>
                  <a href="#ai-intelligence">AI Intelligence</a>
                  <a href="#analytics">Analytics</a>
                  <a href="#opportunities">Opportunities</a>
                  <a href="#grounded-assistant">Assistant</a>
                </nav>
                """,
                unsafe_allow_html=True,
            )
            if st.session_state.get(CHAT_HISTORY_STATE_KEY):
                if st.button("Clear conversation", key="sidebar_clear_conversation", width="stretch"):
                    clear_conversation(st.session_state)
                    st.rerun()
        return settings, enabled
    except (ValidationError, ValueError):
        with st.sidebar:
            st.markdown('<div class="prismops-sidebar-brand">PrismOps</div>', unsafe_allow_html=True)
            st.markdown('<span class="prismops-status-badge off">AI · Setup required</span>', unsafe_allow_html=True)
            st.caption("Invalid local model configuration. See README.")
        return None, False


def _handle_company_change() -> None:
    clear_company_results(st.session_state)


def _run_deterministic_audit(company_id: str, company_name: str) -> None:
    try:
        with st.spinner(f"Validating {company_name} data and calculating support metrics…"):
            st.session_state[AUDIT_STATE_KEY] = run_support_audit(company_id=company_id)
            clear_ai_results(st.session_state)
    except DemoDataValidationError as exc:
        st.session_state.pop(AUDIT_STATE_KEY, None)
        st.error(
            f"The {company_name} demo files are missing or invalid. "
            f"Correct the demo inputs and try again. Details: {exc}"
        )
    except Exception:
        st.session_state.pop(AUDIT_STATE_KEY, None)
        st.error("The deterministic audit could not be completed. Verify the demo files and try again.")


def _render_dashboard(
    audit: SupportAudit, *, ai_enabled: bool, max_chat_messages: int
) -> None:
    _render_ai_features(audit, ai_enabled=ai_enabled)
    st.divider()
    render_executive_overview(audit)
    st.divider()
    render_visualizations(audit)
    st.divider()
    render_opportunity_ranking(audit)
    st.divider()
    render_category_analysis(audit)
    st.divider()
    render_process_documentation(audit)
    st.divider()
    render_scoring_methodology()
    st.divider()
    _render_grounded_assistant(
        ai_enabled=ai_enabled, max_chat_messages=max_chat_messages
    )


def _render_ai_features(audit: SupportAudit, *, ai_enabled: bool) -> None:
    grounded = st.session_state.get(AI_RESULT_STATE_KEY)
    initial_report = st.session_state.get(AI_REPORT_STATE_KEY)
    refined = st.session_state.get(REFINED_REPORT_STATE_KEY)
    questions = st.session_state.get(CLARIFICATION_QUESTIONS_STATE_KEY)
    question_count = len(questions.questions) if isinstance(questions, ClarificationQuestionBatch) else 0
    statuses = (
        "Completed" if isinstance(initial_report, ExecutiveAuditReport) else ("Ready" if ai_enabled else "Unavailable"),
        ("Completed" if isinstance(refined, ExecutiveAuditReport) else f"{question_count} questions pending") if question_count else "Not generated",
        "Completed" if isinstance(refined, ExecutiveAuditReport) else "Not generated",
        "Ready" if isinstance(initial_report, ExecutiveAuditReport) and ai_enabled else "Unavailable",
    )
    steps = ("Initial Report", "Clarifications", "Refined Report", "Audit Chat")
    workflow = "".join(
        f'<div class="prismops-step"><strong><span class="prismops-step-badge">{index}</span>{label}</strong><span>{status}</span></div>'
        for index, (label, status) in enumerate(zip(steps, statuses, strict=True), start=1)
    )
    st.markdown(
        '<div id="ai-intelligence" class="prismops-section-anchor"><div class="prismops-section-kicker">GROUNDED REASONING</div></div>',
        unsafe_allow_html=True,
    )
    st.subheader("AI Intelligence")
    st.markdown(
        f"""
        <div class="prismops-ai-panel">
          <div class="prismops-ai-panel-inner">
            <p>Verified metrics remain canonical. AI interprets those facts, documents assumptions, and preserves human review.</p>
            <div class="prismops-workflow">{workflow}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not ai_enabled:
        st.markdown(
            '<div class="prismops-setup-card"><strong>AI setup required</strong><br>Copy <code>.env.example</code> to <code>.env</code> and add your own OpenAI API key. All deterministic analytics remain available.</div>',
            unsafe_allow_html=True,
        )
    else:
        action_label = (
            "Regenerate Initial Report"
            if isinstance(initial_report, ExecutiveAuditReport)
            else "Generate AI Recommendations"
        )
        action_type = (
            "secondary"
            if isinstance(initial_report, ExecutiveAuditReport)
            else "primary"
        )
        if st.button(action_label, type=action_type, key="generate_ai_report"):
            _generate_initial_ai_result(audit, ai_enabled=ai_enabled)

    grounded = st.session_state.get(AI_RESULT_STATE_KEY)
    initial_report = st.session_state.get(AI_REPORT_STATE_KEY)
    refined = st.session_state.get(REFINED_REPORT_STATE_KEY)
    questions = st.session_state.get(CLARIFICATION_QUESTIONS_STATE_KEY)

    if not isinstance(grounded, GroundedAuditResult) or not isinstance(
        initial_report, ExecutiveAuditReport
    ):
        return

    st.markdown("### Initial Recommendations")
    render_ai_report(initial_report)
    if isinstance(questions, ClarificationQuestionBatch):
        existing = {
            item.question_id: item.answer
            for item in st.session_state.get(CLARIFICATION_ANSWERS_STATE_KEY, [])
            if isinstance(item, StakeholderClarification)
        }
        submitted, answers = render_clarification_form(questions, existing)
        if submitted:
            _refine_recommendations(grounded, answers, ai_enabled=ai_enabled)

    if isinstance(refined, ExecutiveAuditReport):
        st.markdown("### Refined Report")
        st.caption("Uses optional stakeholder clarification without changing canonical metrics.")
        render_ai_report(refined)


def _generate_initial_ai_result(audit: SupportAudit, *, ai_enabled: bool) -> None:
    if not ai_enabled:
        return
    try:
        with st.spinner("Interpreting verified metrics and documented workflows…"):
            result = run_ai_support_audit_result(audit_supplier=lambda: audit)
        st.session_state[AI_RESULT_STATE_KEY] = result
        st.session_state[AI_REPORT_STATE_KEY] = result.report
        st.session_state[CLARIFICATION_QUESTIONS_STATE_KEY] = result.clarification_questions
        st.session_state[CLARIFICATION_ANSWERS_STATE_KEY] = []
        st.session_state.pop(REFINED_REPORT_STATE_KEY, None)
        clear_conversation(st.session_state)
        st.success("Initial report verified. Clarification questions are ready.")
    except Exception as exc:
        _render_ai_error(exc)


def _refine_recommendations(
    grounded: GroundedAuditResult,
    answers: dict[str, str],
    *,
    ai_enabled: bool,
) -> None:
    if not ai_enabled:
        st.info("AI features are disabled until a local OpenAI API key is configured.")
        return
    try:
        with st.spinner("Refining recommendations with stakeholder context…"):
            report, validated_answers = refine_audit_report(
                client=create_structured_output_client(),
                grounded_result=grounded,
                answers=answers,
            )
        st.session_state[CLARIFICATION_ANSWERS_STATE_KEY] = validated_answers
        st.session_state[REFINED_REPORT_STATE_KEY] = report
        clear_conversation(st.session_state)
        st.success("Refined report verified against the original audit evidence.")
    except ClarificationContradictionError as exc:
        st.error(str(exc))
    except Exception as exc:
        _render_ai_error(exc)


def _render_grounded_assistant(
    *, ai_enabled: bool, max_chat_messages: int
) -> None:
    st.markdown('<div id="grounded-assistant" class="prismops-section-anchor"><div class="prismops-section-kicker">SESSION-ONLY EVIDENCE Q&amp;A</div></div>', unsafe_allow_html=True)
    st.subheader("Grounded Audit Assistant")
    grounded = st.session_state.get(AI_RESULT_STATE_KEY)
    initial_report = st.session_state.get(AI_REPORT_STATE_KEY)
    refined = st.session_state.get(REFINED_REPORT_STATE_KEY)
    if not isinstance(grounded, GroundedAuditResult) or not isinstance(initial_report, ExecutiveAuditReport):
        st.caption("Generate the initial AI report to unlock audit-aware questions. No chat input is active yet.")
        return
    report = refined if isinstance(refined, ExecutiveAuditReport) else initial_report
    _render_chat(
        grounded,
        report=report,
        ai_enabled=ai_enabled,
        max_chat_messages=max_chat_messages,
    )


def _render_chat(
    grounded: GroundedAuditResult,
    *,
    report: ExecutiveAuditReport,
    ai_enabled: bool,
    max_chat_messages: int,
) -> None:
    st.caption(
        "Session-only assistant grounded in verified metrics, documented processes, "
        "recommendations, and optional clarification. It cannot access raw tickets or execute work."
    )
    st.caption("Try: Why is Order Status ranked first? · Which recommendation has the strongest evidence? · What information is still missing?")
    history = st.session_state.setdefault(CHAT_HISTORY_STATE_KEY, [])
    if history and st.button("Clear Conversation", key="assistant_clear_conversation"):
        clear_conversation(st.session_state)
        history = []
    render_chat_history(history)
    if not ai_enabled:
        return
    with st.container(border=True):
        question = st.chat_input(
            "Ask a grounded question about the completed support audit",
            key="grounded_audit_chat_input",
        )
    if question is None:
        return
    if not question.strip():
        st.warning("Enter a question before sending.")
        return

    try:
        clarifications = st.session_state.get(CLARIFICATION_ANSWERS_STATE_KEY, [])
        context = build_chat_context(
            grounded_result=grounded,
            report=report,
            clarification_answers=clarifications,
            history=history,
            max_messages=max_chat_messages,
        )
        with st.spinner("Reviewing the verified audit evidence…"):
            answer = answer_audit_question(
                client=create_structured_output_client(),
                context=context,
                question=question,
            )
        history.extend(
            [
                ChatTurn(role="user", content=question),
                ChatTurn(role="assistant", content=answer.answer, answer_details=answer),
            ]
        )
        st.session_state[CHAT_HISTORY_STATE_KEY] = history[-max_chat_messages:]
        st.rerun()
    except (ChatGroundingError, ValueError) as exc:
        st.error(f"The chat response failed grounding validation: {exc}")
    except Exception as exc:
        _render_ai_error(exc)


def _render_ai_error(exc: Exception) -> None:
    if isinstance(exc, LLMConfigurationError):
        st.error("AI configuration is incomplete. Add your own OpenAI API key to the root `.env` file.")
    elif isinstance(exc, LLMAuthenticationError):
        st.error("The configured OpenAI API key was rejected. Verify or replace the local key.")
    elif isinstance(exc, LLMQuotaError):
        st.error("OpenAI quota or billing limits prevented this request. Review your API account.")
    elif isinstance(exc, LLMRateLimitError):
        st.error("OpenAI is temporarily rate limiting requests. Please retry shortly.")
    elif isinstance(exc, LLMTimeoutError):
        st.error("The model request timed out. Please retry.")
    elif isinstance(exc, LLMNetworkError):
        st.error("PrismOps could not reach OpenAI. Check your network and retry.")
    elif isinstance(exc, LLMUnsupportedModelError):
        st.error("The configured model is unavailable. Check `PRISMOPS_LLM_MODEL` in `.env`.")
    elif isinstance(exc, MalformedStructuredOutputError):
        st.error("The model returned malformed structured output. No unverified result was displayed.")
    elif isinstance(exc, GraphValidationError):
        st.error("The AI result failed evidence validation. No unverified result was displayed.")
    elif isinstance(exc, LLMProviderError):
        st.error("The model provider could not complete the request. Please retry later.")
    else:
        st.error("The AI request could not be completed. The deterministic audit remains available.")
