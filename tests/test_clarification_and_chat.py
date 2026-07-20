"""Tests for clarification, refinement, and bounded grounded chat."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from prismops.agents.graph import (
    build_evidence_package,
    validate_clarification_questions,
)
from prismops.models.ai_audit import (
    AuditChatAnswer,
    AutomationRecommendation,
    ChatTurn,
    ClarificationQuestion,
    ClarificationQuestionBatch,
    ExecutiveAuditReport,
    ExecutiveNarrative,
    GroundedAuditResult,
    ProcessAnalysis,
    RecommendationBatch,
)
from prismops.services.ai_interactions import (
    ChatGroundingError,
    ClarificationContradictionError,
    answer_audit_question,
    build_chat_context,
    refine_audit_report,
    validate_clarification_answers,
)
from prismops.services import run_support_audit


@pytest.fixture(scope="module")
def grounded() -> GroundedAuditResult:
    audit = run_support_audit()
    evidence = build_evidence_package(audit)
    process = [
        ProcessAnalysis(
            category=item.metrics.category.value,
            repetitive_steps=["Review documented request"],
            systems_used=["Support inbox"],
            exception_cases=["Missing identifier"],
            human_approval_required=True,
            observations=["Manual review is documented"],
        )
        for item in evidence.categories
    ]
    recommendation = _recommendation(
        "order status", evidence.categories[0].allowed_numeric_evidence[:2]
    )
    return GroundedAuditResult(
        evidence=evidence,
        process_analysis=process,
        report=ExecutiveAuditReport(
            executive_summary="A bounded pilot may be evaluated.",
            recommendations=[recommendation],
            limitations=["Operational validation remains necessary."],
        ),
        clarification_questions=ClarificationQuestionBatch(
            questions=[
                ClarificationQuestion(
                    question_id="access",
                    question="Can agents access order and carrier status in an approved workflow?",
                    rationale="Access determines whether decision support is feasible.",
                    related_categories=["order status"],
                )
            ]
        ),
    )


def test_no_more_than_three_clarification_questions() -> None:
    question = ClarificationQuestion(
        question_id="access",
        question="Can agents access the approved order system during support work?",
        rationale="System access determines whether assistance is feasible.",
        related_categories=["order status"],
    )
    with pytest.raises(ValidationError):
        ClarificationQuestionBatch(questions=[question] * 4)


def test_questions_requesting_existing_metrics_are_rejected(grounded) -> None:
    batch = ClarificationQuestionBatch(
        questions=[
            ClarificationQuestion(
                question_id="known_metric",
                question="What is the ticket count for order status requests?",
                rationale="This would duplicate existing deterministic evidence.",
                related_categories=["order status"],
            )
        ]
    )
    accepted, issues = validate_clarification_questions(batch, grounded.evidence)
    assert accepted.questions == []
    assert "canonical metric" in issues[0]


def test_questions_do_not_repeat_documented_process_content(grounded) -> None:
    batch = ClarificationQuestionBatch(
        questions=[
            ClarificationQuestion(
                question_id="known_systems",
                question="Which systems are used for the order status workflow?",
                rationale="This is already available in supplied process documentation.",
                related_categories=["order status"],
            )
        ]
    )
    accepted, issues = validate_clarification_questions(batch, grounded.evidence)
    assert accepted.questions == []
    assert "documented information" in issues[0]


def test_clarification_answers_are_separately_labeled(grounded) -> None:
    answers = validate_clarification_answers(
        grounded.clarification_questions,
        {"access": "Agents have read-only access after supervisor approval."},
    )
    assert answers[0].source_label == "stakeholder-provided clarification"
    assert "read-only" in answers[0].answer


def test_clarification_cannot_overwrite_metrics(grounded) -> None:
    with pytest.raises(ClarificationContradictionError):
        validate_clarification_answers(
            grounded.clarification_questions,
            {"access": "The ticket count is 42."},
        )


def test_refinement_preserves_original_audit(grounded) -> None:
    before = grounded.evidence.model_dump_json()
    client = RefinementFake(grounded)
    report, answers = refine_audit_report(
        client=client,
        grounded_result=grounded,
        answers={"access": "Agents have approved read-only access."},
    )
    assert grounded.evidence.model_dump_json() == before
    assert report.recommendations[0].evidence == grounded.evidence.categories[0].allowed_numeric_evidence[:2]
    assert answers[0].source_label == "stakeholder-provided clarification"


def test_chat_context_is_bounded_and_excludes_raw_rows(grounded) -> None:
    history = [ChatTurn(role="user", content=f"Question {index}") for index in range(10)]
    context = build_chat_context(
        grounded_result=grounded, history=history, max_messages=3
    )
    serialized = context.model_dump_json()
    assert len(context.recent_turns) == 3
    assert context.recent_turns[0].content == "Question 7"
    assert "ticket_id" not in serialized
    assert "created_at" not in serialized
    assert "Customer requests an update" not in serialized


def test_chat_answer_retains_structured_fields(grounded) -> None:
    context = build_chat_context(grounded_result=grounded)
    evidence = grounded.evidence.categories[0].allowed_numeric_evidence[0]
    expected = AuditChatAnswer(
        answer=f"The canonical evidence is {evidence}.",
        evidence_used=[evidence],
        assumptions=["General technical knowledge: repetitive lookups can suit decision support."],
        missing_information=["Approved system access is not documented."],
    )
    answer = answer_audit_question(
        client=SingleResponseFake(expected), context=context, question="Why was this ranked first?"
    )
    assert answer == expected


def test_unsupported_company_claim_is_rejected(grounded) -> None:
    context = build_chat_context(grounded_result=grounded)
    unsupported = AuditChatAnswer(
        answer="Northstar uses a proprietary fulfillment API.",
        evidence_used=["Northstar uses a proprietary fulfillment API."],
        assumptions=[],
        missing_information=[],
    )
    with pytest.raises(ChatGroundingError):
        answer_audit_question(
            client=SingleResponseFake(unsupported), context=context, question="Which API is used?"
        )


def test_empty_chat_input_is_rejected(grounded) -> None:
    context = build_chat_context(grounded_result=grounded)
    with pytest.raises(ValueError, match="must not be empty"):
        answer_audit_question(
            client=SingleResponseFake(None), context=context, question="   "
        )


def test_unknown_answer_must_label_missing_information(grounded) -> None:
    context = build_chat_context(grounded_result=grounded)
    unknown = AuditChatAnswer(
        answer="The available evidence does not identify an approved API.",
        evidence_used=[],
        assumptions=[],
        missing_information=["Approved API availability is not documented."],
    )
    assert answer_audit_question(
        client=SingleResponseFake(unknown), context=context, question="Which API is approved?"
    ) == unknown


class SingleResponseFake:
    def __init__(self, response: Any) -> None:
        self.response = response

    def generate(self, *, prompt: str, schema: type[Any]):
        return self.response


class RefinementFake:
    def __init__(self, grounded: GroundedAuditResult) -> None:
        self.grounded = grounded

    def generate(self, *, prompt: str, schema: type[Any]):
        if schema is RecommendationBatch:
            return RecommendationBatch(
                recommendations=[
                    _recommendation(
                        "order status",
                        self.grounded.evidence.categories[0].allowed_numeric_evidence[:2],
                    )
                ]
            )
        if schema is ExecutiveNarrative:
            return ExecutiveNarrative(
                executive_summary="The refined recommendation remains bounded.",
                limitations=["Stakeholder context is not deterministic evidence."],
            )
        raise AssertionError(schema)


def _recommendation(category: str, evidence: list[str]) -> AutomationRecommendation:
    return AutomationRecommendation(
        category=category,
        title="Draft routine status responses",
        current_workflow="Agents review order and carrier information",
        proposed_automation="Prepare a response for agent approval",
        evidence=evidence,
        expected_benefits=["Reduce repetitive lookup effort"],
        assumptions=["Stakeholder clarification: approved read access is available"],
        risks=["Carrier information may be stale"],
        human_review_points=["Review exception shipments"],
        confidence="medium",
    )
