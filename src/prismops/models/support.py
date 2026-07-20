"""Domain models for the customer-support operations module."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class TicketCategory(StrEnum):
    ORDER_STATUS = "order status"
    BILLING_QUESTION = "billing question"
    RETURN_REQUEST = "return request"
    ACCOUNT_ACCESS = "account access"
    DAMAGED_SHIPMENT = "damaged shipment"
    PRODUCT_QUESTION = "product question"
    MISCELLANEOUS = "miscellaneous"
    APPOINTMENT_SCHEDULING = "appointment scheduling"
    INSURANCE_ELIGIBILITY = "insurance eligibility"
    PORTAL_ACCESS = "portal access"
    REFERRAL_STATUS = "referral status"
    PRESCRIPTION_REFILL_REQUEST = "prescription refill request"
    MEDICAL_RECORDS_REQUEST = "medical records request"
    GENERAL_INQUIRY = "general inquiry"
    ORDER_TRACKING = "order tracking"
    REFUND_STATUS = "refund status"
    PROMOTION_QUESTION = "promotion question"
    SUBSCRIPTION_CHANGE = "subscription change"
    FRAUD_REVIEW = "fraud review"


class SupportTicket(BaseModel):
    ticket_id: str
    created_at: datetime
    category: TicketCategory
    description: str = Field(min_length=1)
    resolution_minutes: float = Field(ge=0)
    escalated: bool
    channel: str = Field(min_length=1)
    customer_tier: str = Field(min_length=1)


class DemoCompany(BaseModel):
    id: str
    name: str
    industry: str
    description: str
    headquarters: str
    support_team_size: int = Field(gt=0)
    support_hours: str
    reporting_period_start: date
    reporting_period_end: date
    disclaimer: str
    ticket_count: int = Field(default=3_000, gt=0)
    demo_status: str = "Preloaded fictional demo"


class CategoryMetrics(BaseModel):
    category: TicketCategory
    ticket_count: int
    category_percentage: float
    average_resolution_minutes: float
    total_handling_hours: float
    escalation_rate: float
    automation_score: float = Field(ge=0, le=100)


class DimensionCount(BaseModel):
    value: str
    ticket_count: int


class SupportSummary(BaseModel):
    total_ticket_count: int
    total_handling_hours: float
    overall_escalation_rate: float
    by_category: list[CategoryMetrics]
    by_channel: list[DimensionCount]
    by_customer_tier: list[DimensionCount]


class AutomationOpportunity(BaseModel):
    rank: int = Field(gt=0)
    metrics: CategoryMetrics
    explanation: str


class SupportAudit(BaseModel):
    company: DemoCompany
    summary: SupportSummary
    opportunities: list[AutomationOpportunity]
    process_documentation: str
    highest_volume_category: TicketCategory
    highest_automation_category: TicketCategory
