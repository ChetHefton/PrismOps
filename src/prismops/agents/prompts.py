"""Prompt templates for the grounded support-audit workflow."""

from __future__ import annotations

from prismops.models.ai_audit import (
    AuditChatContext,
    AutomationRecommendation,
    ExecutiveAuditReport,
    ProcessAnalysis,
    StakeholderClarification,
    SupportEvidencePackage,
)

GROUNDING_RULES = """Use only the supplied selected-company evidence.
Do not perform arithmetic or recreate any metric.
Do not invent company-specific facts, APIs, systems, permissions, costs, staffing, or timelines.
Label assumptions explicitly and admit when information is insufficient.
Treat numeric strings supplied by Python as immutable quotations.
Recommend decision support rather than fully autonomous action when risks or exceptions are significant.
Never claim guaranteed savings or outcomes."""


def process_analysis_prompt(evidence: SupportEvidencePackage) -> str:
    return f"""Analyze the documented workflows for every category in the evidence package.
Identify repetitive steps, manual handoffs, named systems, exception paths, and whether human approval is required.
Return one structured analysis per existing category.

{GROUNDING_RULES}

EVIDENCE PACKAGE:
{evidence.model_dump_json(indent=2)}"""


def recommendations_prompt(
    evidence: SupportEvidencePackage, process_analysis: list[ProcessAnalysis]
) -> str:
    allowed_lines = {
        item.metrics.category.value: item.allowed_numeric_evidence
        for item in evidence.categories
    }
    analyses_json = "[" + ",".join(item.model_dump_json() for item in process_analysis) + "]"
    return f"""Generate at most three preliminary automation recommendations.
Tie each recommendation to one existing category. Prefer strong deterministic metrics plus a consistent documented process.
The evidence list must contain at least two exact, unchanged strings copied from ALLOWED NUMERIC EVIDENCE for that category.
Put no numeric claims anywhere else. Separate evidence from assumptions. Include risks and concrete human-review points.

{GROUNDING_RULES}

COMPANY: {evidence.company.name}

ALLOWED NUMERIC EVIDENCE:
{allowed_lines}

DETERMINISTIC CATEGORY EVIDENCE:
{[item.model_dump(mode="json", exclude={"allowed_numeric_evidence"}) for item in evidence.categories]}

PROCESS ANALYSIS:
{analyses_json}"""


def executive_report_prompt(
    evidence: SupportEvidencePackage,
    recommendations: list[AutomationRecommendation],
) -> str:
    return f"""Write a concise executive summary and limitations for the verified recommendations.
Do not rewrite, add to, or recalculate recommendation evidence. Put no new numeric claims in the summary.
Make clear that analytics and scores are deterministic while recommendations are AI interpretations requiring validation.

{GROUNDING_RULES}

COMPANY: {evidence.company.name}
VERIFIED RECOMMENDATIONS:
{[item.model_dump(mode="json") for item in recommendations]}"""


def clarification_questions_prompt(
    evidence: SupportEvidencePackage,
    process_analysis: list[ProcessAnalysis],
    report: ExecutiveAuditReport,
) -> str:
    return f"""Generate no more than three specific, optional clarification questions that would materially improve the verified recommendations.
Focus only on missing operational facts such as access, approvals, exception frequency, authority, verification, data availability, handoffs, security, or compliance.
Do not request ticket counts, percentages, averages, handling hours, escalation rates, automation scores, or anything already documented.
Do not ask vague questions. Explain why each answer matters. Use only audited category names.

{GROUNDING_RULES}

EVIDENCE:
{evidence.model_dump_json()}

PROCESS ANALYSIS:
{[item.model_dump(mode="json") for item in process_analysis]}

VERIFIED REPORT:
{report.model_dump_json()}"""


def refinement_prompt(
    evidence: SupportEvidencePackage,
    process_analysis: list[ProcessAnalysis],
    original_report: ExecutiveAuditReport,
    clarifications: list[StakeholderClarification],
) -> str:
    return f"""Refine the recommendations using optional stakeholder clarification.
Generate at most three recommendations. Preserve canonical deterministic metrics exactly.
Stakeholder answers are context, not verified evidence, and may appear only as labeled assumptions or operational constraints.
The evidence list must contain at least two exact canonical evidence strings for each category.
Put no numeric claims outside exact evidence strings. Include risks and human-review points.

{GROUNDING_RULES}

CANONICAL EVIDENCE:
{evidence.model_dump_json()}

PROCESS ANALYSIS:
{[item.model_dump(mode="json") for item in process_analysis]}

ORIGINAL VERIFIED REPORT:
{original_report.model_dump_json()}

STAKEHOLDER-PROVIDED CLARIFICATION:
{[item.model_dump(mode="json") for item in clarifications]}"""


def chat_prompt(context: AuditChatContext, question: str) -> str:
    return f"""Answer the user's question about the completed support audit for {context.company_name}.
Use only the supplied audit context. Do not access raw tickets, execute SQL, modify the audit, or claim guaranteed outcomes.
When discussing a metric, cite exact unchanged lines from EVIDENCE CATALOG in evidence_used and do not recalculate it.
Every evidence_used entry must be copied exactly from EVIDENCE CATALOG.
Distinguish rules-based automation scores from AI recommendations.
If evidence is insufficient, say so and list the gap in missing_information.
Label general technical knowledge in assumptions as 'General technical knowledge: ...'.
Do not invent systems, APIs, permissions, costs, timelines, staffing, or company facts.
Recommend human review for high-risk decisions.

{GROUNDING_RULES}

BOUNDED AUDIT CONTEXT:
{context.model_dump_json()}

USER QUESTION:
{question}"""
