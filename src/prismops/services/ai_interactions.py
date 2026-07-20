"""Grounded clarification, refinement, and bounded audit-chat services."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from prismops.agents.graph import GraphValidationError, verify_recommendations
from prismops.agents.prompts import chat_prompt, executive_report_prompt, refinement_prompt
from prismops.agents.provider import StructuredOutputClient
from prismops.models.ai_audit import (
    AuditChatAnswer,
    AuditChatContext,
    ChatTurn,
    ClarificationQuestionBatch,
    ExecutiveAuditReport,
    ExecutiveNarrative,
    GroundedAuditResult,
    RecommendationBatch,
    StakeholderClarification,
    SupportEvidencePackage,
)

CANONICAL_METRIC_TERMS = (
    "ticket count",
    "category percentage",
    "average resolution",
    "resolution minutes",
    "handling hours",
    "escalation rate",
    "automation score",
)
NUMBER_TOKEN = re.compile(r"\d[\d,]*(?:\.\d+)?%?(?:/\d+)?")


class ClarificationContradictionError(ValueError):
    """Raised when stakeholder context attempts to redefine canonical metrics."""


class ChatGroundingError(ValueError):
    """Raised when a structured chat answer is unsupported by its context."""


def validate_clarification_answers(
    questions: ClarificationQuestionBatch,
    answers: Mapping[str, str],
) -> list[StakeholderClarification]:
    """Label non-empty answers and reject attempts to overwrite audit metrics."""

    question_by_id = {item.question_id: item for item in questions.questions}
    validated: list[StakeholderClarification] = []
    for question_id, raw_answer in answers.items():
        answer = raw_answer.strip()
        if not answer or question_id not in question_by_id:
            continue
        lowered = answer.lower()
        if NUMBER_TOKEN.search(answer) and any(
            term in lowered for term in CANONICAL_METRIC_TERMS
        ):
            raise ClarificationContradictionError(
                "Stakeholder clarification cannot overwrite canonical audit metrics."
            )
        question = question_by_id[question_id]
        validated.append(
            StakeholderClarification(
                question_id=question_id,
                question=question.question,
                answer=answer,
            )
        )
    return validated


def refine_audit_report(
    *,
    client: StructuredOutputClient,
    grounded_result: GroundedAuditResult,
    answers: Mapping[str, str],
) -> tuple[ExecutiveAuditReport, list[StakeholderClarification]]:
    """Refine recommendations without rerunning or mutating deterministic analytics."""

    clarifications = validate_clarification_answers(
        grounded_result.clarification_questions, answers
    )
    draft = client.generate(
        prompt=refinement_prompt(
            grounded_result.evidence,
            grounded_result.process_analysis,
            grounded_result.report,
            clarifications,
        ),
        schema=RecommendationBatch,
    )
    verified, issues = verify_recommendations(draft, grounded_result.evidence)
    if not verified:
        raise GraphValidationError(
            "No refined recommendations passed deterministic evidence validation."
        )
    narrative = client.generate(
        prompt=executive_report_prompt(grounded_result.evidence, verified),
        schema=ExecutiveNarrative,
    )
    report = ExecutiveAuditReport(
        executive_summary=narrative.executive_summary,
        recommendations=verified,
        limitations=[*narrative.limitations, *issues],
    )
    return report, clarifications


def build_chat_context(
    *,
    grounded_result: GroundedAuditResult,
    report: ExecutiveAuditReport | None = None,
    clarification_answers: Sequence[StakeholderClarification] = (),
    history: Sequence[ChatTurn] = (),
    max_messages: int = 6,
) -> AuditChatContext:
    """Build bounded, row-free context from verified audit artifacts."""

    if max_messages < 1:
        raise ValueError("max_messages must be at least 1")
    active_report = report or grounded_result.report
    catalog = _evidence_catalog(
        grounded_result.evidence,
        grounded_result.process_analysis,
        active_report,
    )
    return AuditChatContext(
        company_name=grounded_result.evidence.company.name,
        audit_summary=grounded_result.evidence.audit_summary,
        category_evidence=grounded_result.evidence.categories,
        scoring_methodology=grounded_result.evidence.scoring_methodology,
        process_documentation=grounded_result.evidence.process_documentation,
        process_analysis=grounded_result.process_analysis,
        executive_summary=active_report.executive_summary,
        report_limitations=active_report.limitations,
        recommendations=active_report.recommendations,
        clarification_answers=list(clarification_answers),
        evidence_catalog=catalog,
        recent_turns=list(history[-max_messages:]),
    )


def answer_audit_question(
    *,
    client: StructuredOutputClient,
    context: AuditChatContext,
    question: str,
) -> AuditChatAnswer:
    """Generate and deterministically validate one grounded chat response."""

    question = question.strip()
    if not question:
        raise ValueError("Chat question must not be empty")
    answer = client.generate(prompt=chat_prompt(context, question), schema=AuditChatAnswer)
    allowed = set(context.evidence_catalog)
    if any(item not in allowed for item in answer.evidence_used):
        raise ChatGroundingError(
            "The chat response referenced evidence outside the verified audit context."
        )
    if not answer.evidence_used and not answer.missing_information:
        raise ChatGroundingError(
            "The chat response supplied neither verified evidence nor an explicit information gap."
        )
    allowed_assumption_labels = (
        "General technical knowledge:",
        "Model assumption:",
        "Stakeholder clarification:",
    )
    if any(
        not assumption.startswith(allowed_assumption_labels)
        for assumption in answer.assumptions
    ):
        raise ChatGroundingError(
            "The chat response included an assumption without a source label."
        )
    numeric_tokens = NUMBER_TOKEN.findall(answer.answer)
    cited_text = " ".join(answer.evidence_used)
    if any(token not in cited_text for token in numeric_tokens):
        raise ChatGroundingError(
            "The chat response included a numeric claim without canonical evidence."
        )
    if "guarantee" in answer.answer.lower():
        raise ChatGroundingError("The chat response claimed an unsupported guarantee.")
    return answer


def _evidence_catalog(
    evidence: SupportEvidencePackage,
    process_analysis,
    report: ExecutiveAuditReport,
) -> list[str]:
    catalog: list[str] = []
    for category in evidence.categories:
        catalog.extend(category.allowed_numeric_evidence)
        catalog.append(
            f"Deterministic ranking — {category.metrics.category.value}: {category.deterministic_explanation}"
        )
    for analysis in process_analysis:
        for value in analysis.repetitive_steps:
            catalog.append(f"Process documentation — {analysis.category} — repetitive step: {value}")
        for value in analysis.systems_used:
            catalog.append(f"Process documentation — {analysis.category} — system: {value}")
        for value in analysis.exception_cases:
            catalog.append(f"Process documentation — {analysis.category} — exception: {value}")
    for recommendation in report.recommendations:
        catalog.append(
            f"Verified recommendation — {recommendation.category} — title: {recommendation.title}"
        )
        for value in recommendation.risks:
            catalog.append(f"Verified recommendation — {recommendation.category} — risk: {value}")
        for value in recommendation.human_review_points:
            catalog.append(
                f"Verified recommendation — {recommendation.category} — human review: {value}"
            )
    for line in evidence.process_documentation.splitlines():
        if line.startswith("- **"):
            catalog.append(f"Process documentation — {line[2:]}")
    return list(dict.fromkeys(catalog))
