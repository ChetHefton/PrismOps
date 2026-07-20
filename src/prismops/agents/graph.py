"""Linear LangGraph workflow for grounded demo-company support recommendations."""

from __future__ import annotations

import re
from collections.abc import Callable

from langgraph.graph import END, START, StateGraph

from prismops.agents.prompts import (
    clarification_questions_prompt,
    executive_report_prompt,
    process_analysis_prompt,
    recommendations_prompt,
)
from prismops.agents.provider import (
    StructuredOutputClient,
    create_structured_output_client,
)
from prismops.agents.state import SupportAuditGraphState
from prismops.models.ai_audit import (
    AutomationRecommendation,
    CategoryEvidence,
    ClarificationQuestion,
    ClarificationQuestionBatch,
    ExecutiveAuditReport,
    ExecutiveNarrative,
    GroundedAuditResult,
    ProcessAnalysis,
    ProcessAnalysisBatch,
    RecommendationBatch,
    ScoringMethodology,
    SupportEvidencePackage,
)
from prismops.models.support import CategoryMetrics, SupportAudit
from prismops.services.support_audit import run_support_audit

AuditSupplier = Callable[[], SupportAudit]
NUMBER_PATTERN = re.compile(r"\d")
KNOWN_METRIC_REQUESTS = (
    "ticket count",
    "how many tickets",
    "category percentage",
    "average resolution",
    "resolution minutes",
    "handling hours",
    "escalation rate",
    "automation score",
)
VAGUE_QUESTIONS = ("provide more information", "what are your business goals")
DOCUMENTED_INFORMATION_REQUESTS = (
    "which systems are used",
    "what systems are used",
    "what are the manual steps",
    "what exception cases",
    "which exceptions are documented",
)


class GraphValidationError(RuntimeError):
    """Raised when model output fails deterministic evidence validation."""


def build_evidence_package(audit: SupportAudit) -> SupportEvidencePackage:
    """Convert verified audit results into compact, row-free LLM evidence."""

    ranks = {item.metrics.category: item for item in audit.opportunities}
    categories = []
    for metrics in audit.summary.by_category:
        opportunity = ranks[metrics.category]
        categories.append(
            CategoryEvidence(
                rank=opportunity.rank,
                metrics=metrics,
                deterministic_explanation=opportunity.explanation,
                allowed_numeric_evidence=numeric_evidence_lines(metrics),
            )
        )
    categories.sort(key=lambda item: item.rank)

    return SupportEvidencePackage(
        company=audit.company,
        audit_summary={
            "total_ticket_count": audit.summary.total_ticket_count,
            "total_handling_hours": audit.summary.total_handling_hours,
            "overall_escalation_rate": audit.summary.overall_escalation_rate,
        },
        categories=categories,
        scoring_methodology=ScoringMethodology(
            note=(
                "Rules-based preliminary score. Python calculates it; the LLM must "
                "not recalculate or treat it as a prediction."
            )
        ),
        process_documentation=audit.process_documentation,
    )


def numeric_evidence_lines(metrics: CategoryMetrics) -> list[str]:
    """Render canonical numeric facts that LLM recommendations may quote verbatim."""

    return [
        f"Ticket count: {metrics.ticket_count:,}",
        f"Category percentage: {metrics.category_percentage:.2f}%",
        f"Average resolution minutes: {metrics.average_resolution_minutes:.2f}",
        f"Total handling hours: {metrics.total_handling_hours:.2f}",
        f"Escalation rate: {metrics.escalation_rate:.2%}",
        f"Automation score: {metrics.automation_score:.2f}/100",
    ]


def verify_recommendations(
    batch: RecommendationBatch, evidence: SupportEvidencePackage
) -> tuple[list[AutomationRecommendation], list[str]]:
    """Accept only grounded, category-valid recommendations with canonical numbers."""

    evidence_by_category = {
        item.metrics.category.value: set(item.allowed_numeric_evidence)
        for item in evidence.categories
    }
    verified: list[AutomationRecommendation] = []
    issues: list[str] = []
    seen_categories: set[str] = set()

    for recommendation in batch.recommendations[:3]:
        category = recommendation.category
        if category not in evidence_by_category:
            issues.append(f"Rejected unsupported category: {category}")
            continue
        if category in seen_categories:
            issues.append(f"Rejected duplicate category recommendation: {category}")
            continue

        allowed = evidence_by_category[category]
        invalid_evidence = [item for item in recommendation.evidence if item not in allowed]
        if invalid_evidence or len(recommendation.evidence) < 2:
            issues.append(
                f"Rejected {category}: numeric evidence was missing or not an exact verified fact."
            )
            continue

        narrative_values = [
            recommendation.title,
            recommendation.current_workflow,
            recommendation.proposed_automation,
            *recommendation.expected_benefits,
            *recommendation.assumptions,
            *recommendation.risks,
            *recommendation.human_review_points,
        ]
        if any(NUMBER_PATTERN.search(value) for value in narrative_values):
            issues.append(
                f"Rejected {category}: numeric claims must appear only as exact evidence lines."
            )
            continue
        if any("guarantee" in value.lower() for value in narrative_values):
            issues.append(f"Rejected {category}: guaranteed outcomes are unsupported.")
            continue

        seen_categories.add(category)
        verified.append(recommendation)

    return verified, issues


def validate_clarification_questions(
    batch: ClarificationQuestionBatch, evidence: SupportEvidencePackage
) -> tuple[ClarificationQuestionBatch, list[str]]:
    """Remove vague, redundant, or category-unsupported questions."""

    categories = {item.metrics.category.value for item in evidence.categories}
    accepted: list[ClarificationQuestion] = []
    issues: list[str] = []
    seen_ids: set[str] = set()
    for question in batch.questions[:3]:
        lowered = question.question.lower()
        if question.question_id in seen_ids:
            issues.append(f"Rejected duplicate clarification id: {question.question_id}")
            continue
        if any(term in lowered for term in KNOWN_METRIC_REQUESTS):
            issues.append(f"Rejected clarification that requests a canonical metric: {question.question_id}")
            continue
        if any(term in lowered for term in VAGUE_QUESTIONS):
            issues.append(f"Rejected vague clarification: {question.question_id}")
            continue
        if any(term in lowered for term in DOCUMENTED_INFORMATION_REQUESTS):
            issues.append(f"Rejected clarification that requests documented information: {question.question_id}")
            continue
        if not set(question.related_categories).issubset(categories):
            issues.append(f"Rejected clarification with unsupported category: {question.question_id}")
            continue
        seen_ids.add(question.question_id)
        accepted.append(question)
    return ClarificationQuestionBatch(questions=accepted), issues


def build_support_audit_graph(
    client: StructuredOutputClient,
    *,
    audit_supplier: AuditSupplier = run_support_audit,
):
    """Compile the explicit five-node support-audit reasoning graph."""

    def prepare_evidence(_: SupportAuditGraphState) -> SupportAuditGraphState:
        return {"evidence": build_evidence_package(audit_supplier())}

    def analyze_processes(state: SupportAuditGraphState) -> SupportAuditGraphState:
        evidence = state["evidence"]
        result = client.generate(
            prompt=process_analysis_prompt(evidence), schema=ProcessAnalysisBatch
        )
        analyses = result.analyses
        expected = {item.metrics.category.value for item in evidence.categories}
        actual = {item.category for item in analyses}
        if actual != expected or len(analyses) != len(expected):
            raise GraphValidationError(
                "Process analysis must contain exactly one entry for every audited category."
            )
        return {"process_analysis": analyses}

    def generate_recommendations(state: SupportAuditGraphState) -> SupportAuditGraphState:
        result = client.generate(
            prompt=recommendations_prompt(
                state["evidence"], state["process_analysis"]
            ),
            schema=RecommendationBatch,
        )
        return {"draft_recommendations": result}

    def verify_recommendation_node(
        state: SupportAuditGraphState,
    ) -> SupportAuditGraphState:
        verified, issues = verify_recommendations(
            state["draft_recommendations"], state["evidence"]
        )
        if not verified:
            raise GraphValidationError(
                "No recommendations passed deterministic evidence validation."
            )
        return {
            "verified_recommendations": verified,
            "validation_issues": issues,
        }

    def build_executive_report(state: SupportAuditGraphState) -> SupportAuditGraphState:
        narrative = client.generate(
            prompt=executive_report_prompt(
                state["evidence"], state["verified_recommendations"]
            ),
            schema=ExecutiveNarrative,
        )
        report = ExecutiveAuditReport(
            executive_summary=narrative.executive_summary,
            recommendations=state["verified_recommendations"],
            limitations=narrative.limitations,
        )
        return {"executive_summary": narrative.executive_summary, "report": report}

    def generate_clarification_questions(
        state: SupportAuditGraphState,
    ) -> SupportAuditGraphState:
        draft = client.generate(
            prompt=clarification_questions_prompt(
                state["evidence"], state["process_analysis"], state["report"]
            ),
            schema=ClarificationQuestionBatch,
        )
        questions, issues = validate_clarification_questions(draft, state["evidence"])
        return {
            "clarification_questions": questions,
            "validation_issues": [*state.get("validation_issues", []), *issues],
        }

    graph = StateGraph(SupportAuditGraphState)
    graph.add_node("prepare_evidence", prepare_evidence)
    graph.add_node("analyze_processes", analyze_processes)
    graph.add_node("generate_recommendations", generate_recommendations)
    graph.add_node("verify_recommendations", verify_recommendation_node)
    graph.add_node("build_executive_report", build_executive_report)
    graph.add_node("generate_clarification_questions", generate_clarification_questions)
    graph.add_edge(START, "prepare_evidence")
    graph.add_edge("prepare_evidence", "analyze_processes")
    graph.add_edge("analyze_processes", "generate_recommendations")
    graph.add_edge("generate_recommendations", "verify_recommendations")
    graph.add_edge("verify_recommendations", "build_executive_report")
    graph.add_edge("build_executive_report", "generate_clarification_questions")
    graph.add_edge("generate_clarification_questions", END)
    return graph.compile()


def run_ai_support_audit(
    client: StructuredOutputClient | None = None,
    *,
    audit_supplier: AuditSupplier = run_support_audit,
) -> ExecutiveAuditReport:
    """Run the grounded workflow and return its UI-facing report contract."""

    return run_ai_support_audit_result(
        client, audit_supplier=audit_supplier
    ).report


def run_ai_support_audit_result(
    client: StructuredOutputClient | None = None,
    *,
    audit_supplier: AuditSupplier = run_support_audit,
) -> GroundedAuditResult:
    """Run the graph and retain the grounded context needed for refinement and chat."""

    client = client or create_structured_output_client()
    result = build_support_audit_graph(client, audit_supplier=audit_supplier).invoke({})
    required = ("evidence", "process_analysis", "report", "clarification_questions")
    if any(key not in result for key in required):
        raise GraphValidationError("The graph did not produce a complete grounded result.")
    return GroundedAuditResult(
        evidence=result["evidence"],
        process_analysis=result["process_analysis"],
        report=result["report"],
        clarification_questions=result["clarification_questions"],
        validation_issues=result.get("validation_issues", []),
    )
