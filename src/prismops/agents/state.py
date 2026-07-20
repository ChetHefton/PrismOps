"""Typed, JSON-serializable state for the support-audit LangGraph."""

from typing import TypedDict

from prismops.models.ai_audit import (
    AutomationRecommendation,
    ClarificationQuestionBatch,
    ExecutiveAuditReport,
    ProcessAnalysis,
    RecommendationBatch,
    SupportEvidencePackage,
)


class SupportAuditGraphState(TypedDict, total=False):
    evidence: SupportEvidencePackage
    process_analysis: list[ProcessAnalysis]
    draft_recommendations: RecommendationBatch
    verified_recommendations: list[AutomationRecommendation]
    executive_summary: str
    validation_issues: list[str]
    report: ExecutiveAuditReport
    clarification_questions: ClarificationQuestionBatch
