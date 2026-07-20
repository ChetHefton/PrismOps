"""Grounding, state, graph, and UI-contract tests with a fully mocked LLM."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from prismops.agents.graph import (
    build_evidence_package,
    build_support_audit_graph,
    run_ai_support_audit,
    verify_recommendations,
)
from prismops.agents.state import SupportAuditGraphState
from prismops.models.ai_audit import (
    AutomationRecommendation,
    ClarificationQuestion,
    ClarificationQuestionBatch,
    ExecutiveAuditReport,
    ExecutiveNarrative,
    ProcessAnalysis,
    ProcessAnalysisBatch,
    RecommendationBatch,
)
from prismops.services import run_support_audit


@pytest.fixture(scope="module")
def audit():
    return run_support_audit()


@pytest.fixture(scope="module")
def evidence(audit):
    return build_evidence_package(audit)


def test_graph_state_construction(evidence) -> None:
    state = SupportAuditGraphState(evidence=evidence, validation_issues=[])

    assert state["evidence"].company.name == "Northstar Industrial Supply"
    assert state["validation_issues"] == []


def test_evidence_package_is_compact_and_excludes_raw_rows(evidence) -> None:
    serialized = evidence.model_dump_json()

    assert len(evidence.categories) == 7
    assert "ticket_id" not in serialized
    assert "created_at" not in serialized
    assert "Customer requests an update" not in serialized
    assert "support_process" not in serialized
    assert "Automation score:" in serialized


def test_unsupported_category_is_rejected(evidence) -> None:
    batch = RecommendationBatch(
        recommendations=[_recommendation("shipping delay", ["Ticket count: 1"])]
    )

    verified, issues = verify_recommendations(batch, evidence)

    assert verified == []
    assert "unsupported category" in issues[0]


def test_unsupported_numeric_evidence_is_rejected(evidence) -> None:
    batch = RecommendationBatch(
        recommendations=[
            _recommendation(
                "order status",
                ["Ticket count: 999,999", "Automation score: 100.00/100"],
            )
        ]
    )

    verified, issues = verify_recommendations(batch, evidence)

    assert verified == []
    assert "exact verified fact" in issues[0]


def test_verified_recommendation_retains_assumptions_and_risks(evidence) -> None:
    order_evidence = evidence.categories[0].allowed_numeric_evidence[:2]
    recommendation = _recommendation("order status", order_evidence)

    verified, issues = verify_recommendations(
        RecommendationBatch(recommendations=[recommendation]), evidence
    )

    assert issues == []
    assert verified[0].assumptions == ["Order identifiers remain available to agents"]
    assert verified[0].risks == ["Carrier status may be stale"]
    assert verified[0].human_review_points == ["Review split shipments"]


def test_maximum_three_recommendations_is_enforced() -> None:
    with pytest.raises(ValidationError):
        RecommendationBatch(
            recommendations=[
                _recommendation("order status", ["one", "two"]) for _ in range(4)
            ]
        )


def test_graph_compiles_with_expected_nodes(audit) -> None:
    graph = build_support_audit_graph(FakeStructuredClient(audit))

    node_names = set(graph.get_graph().nodes)
    assert {
        "prepare_evidence",
        "analyze_processes",
        "generate_recommendations",
        "verify_recommendations",
        "build_executive_report",
    }.issubset(node_names)


def test_mocked_graph_returns_ui_facing_report(audit) -> None:
    report = run_ai_support_audit(
        FakeStructuredClient(audit), audit_supplier=lambda: audit
    )

    assert isinstance(report, ExecutiveAuditReport)
    assert report.executive_summary
    assert len(report.recommendations) == 1
    assert report.recommendations[0].category == "order status"
    assert report.recommendations[0].evidence
    assert report.limitations


class FakeStructuredClient:
    """Schema-aware local fake; never makes a network request."""

    def __init__(self, audit) -> None:
        self.audit = audit
        self.evidence = build_evidence_package(audit)

    def generate(self, *, prompt: str, schema: type[Any]):
        assert "Northstar" in prompt
        if schema is ProcessAnalysisBatch:
            return ProcessAnalysisBatch(
                analyses=[
                    ProcessAnalysis(
                        category=item.metrics.category.value,
                        repetitive_steps=["Review the documented request"],
                        systems_used=["Support inbox"],
                        exception_cases=["Missing context"],
                        human_approval_required=True,
                        observations=["The process includes manual review"],
                    )
                    for item in self.evidence.categories
                ]
            )
        if schema is RecommendationBatch:
            return RecommendationBatch(
                recommendations=[
                    _recommendation(
                        "order status",
                        self.evidence.categories[0].allowed_numeric_evidence[:2],
                    )
                ]
            )
        if schema is ExecutiveNarrative:
            return ExecutiveNarrative(
                executive_summary=(
                    "Northstar can evaluate a bounded decision-support pilot using verified support evidence."
                ),
                limitations=["Recommendations require operational and security review."],
            )
        if schema is ClarificationQuestionBatch:
            return ClarificationQuestionBatch(
                questions=[
                    ClarificationQuestion(
                        question_id="order_access",
                        question="Can support agents read order and carrier status in one approved workflow?",
                        rationale="Access constraints determine whether assistance can be safely designed.",
                        related_categories=["order status"],
                    )
                ]
            )
        raise AssertionError(f"Unexpected schema: {schema}")


def _recommendation(
    category: str, evidence: list[str]
) -> AutomationRecommendation:
    return AutomationRecommendation(
        category=category,
        title="Assist agents with routine status responses",
        current_workflow="Agents review orders and carrier status manually",
        proposed_automation="Draft a status response for agent approval",
        evidence=evidence,
        expected_benefits=["Reduce repetitive lookup effort"],
        assumptions=["Order identifiers remain available to agents"],
        risks=["Carrier status may be stale"],
        human_review_points=["Review split shipments"],
        confidence="high",
    )
