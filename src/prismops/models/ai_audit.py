"""Structured contracts for grounded AI support-audit reasoning."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from prismops.models.support import CategoryMetrics, DemoCompany


class ScoringMethodology(BaseModel):
    volume_weight: float = 0.30
    repetitiveness_weight: float = 0.25
    handling_time_weight: float = 0.15
    escalation_weight: float = 0.15
    process_consistency_weight: float = 0.15
    note: str


class CategoryEvidence(BaseModel):
    rank: int
    metrics: CategoryMetrics
    deterministic_explanation: str
    allowed_numeric_evidence: list[str]


class SupportEvidencePackage(BaseModel):
    company: DemoCompany
    audit_summary: dict[str, int | float]
    categories: list[CategoryEvidence]
    scoring_methodology: ScoringMethodology
    process_documentation: str


class ProcessAnalysis(BaseModel):
    category: str
    repetitive_steps: list[str]
    systems_used: list[str]
    exception_cases: list[str]
    human_approval_required: bool
    observations: list[str]


class ProcessAnalysisBatch(BaseModel):
    analyses: list[ProcessAnalysis]


class AutomationRecommendation(BaseModel):
    category: str
    title: str = Field(min_length=1)
    current_workflow: str = Field(min_length=1)
    proposed_automation: str = Field(min_length=1)
    evidence: list[str] = Field(min_length=1)
    expected_benefits: list[str] = Field(min_length=1)
    assumptions: list[str] = Field(min_length=1)
    risks: list[str] = Field(min_length=1)
    human_review_points: list[str] = Field(min_length=1)
    confidence: Literal["low", "medium", "high"]


class RecommendationBatch(BaseModel):
    recommendations: list[AutomationRecommendation] = Field(max_length=3)


class ExecutiveNarrative(BaseModel):
    executive_summary: str = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)


class ExecutiveAuditReport(BaseModel):
    executive_summary: str
    recommendations: list[AutomationRecommendation] = Field(max_length=3)
    limitations: list[str]


class ClarificationQuestion(BaseModel):
    question_id: str = Field(pattern=r"^[a-z0-9_-]+$")
    question: str = Field(min_length=10)
    rationale: str = Field(min_length=10)
    related_categories: list[str] = Field(min_length=1)
    required: bool = False


class ClarificationQuestionBatch(BaseModel):
    questions: list[ClarificationQuestion] = Field(max_length=3)


class StakeholderClarification(BaseModel):
    question_id: str
    question: str
    answer: str
    source_label: Literal["stakeholder-provided clarification"] = (
        "stakeholder-provided clarification"
    )


class GroundedAuditResult(BaseModel):
    evidence: SupportEvidencePackage
    process_analysis: list[ProcessAnalysis]
    report: ExecutiveAuditReport
    clarification_questions: ClarificationQuestionBatch
    validation_issues: list[str] = Field(default_factory=list)


class AuditChatAnswer(BaseModel):
    answer: str = Field(min_length=1)
    evidence_used: list[str]
    assumptions: list[str]
    missing_information: list[str]


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    answer_details: AuditChatAnswer | None = None


class AuditChatContext(BaseModel):
    company_name: str
    audit_summary: dict[str, int | float]
    category_evidence: list[CategoryEvidence]
    scoring_methodology: ScoringMethodology
    process_documentation: str
    process_analysis: list[ProcessAnalysis]
    executive_summary: str
    report_limitations: list[str]
    recommendations: list[AutomationRecommendation]
    clarification_answers: list[StakeholderClarification]
    evidence_catalog: list[str]
    recent_turns: list[ChatTurn]
