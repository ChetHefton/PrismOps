"""Deterministic analytics for customer-support operations."""

from __future__ import annotations

import duckdb
import pandas as pd

from prismops.models.support import (
    CategoryMetrics,
    DimensionCount,
    SupportSummary,
)

# These inputs encode only what is explicitly documented in support_process.md.
# They are transparent business assumptions, not learned predictions.
PROCESS_FACTORS = {
    "order status": {"repetitiveness": 1.00, "process_consistency": 1.00},
    "billing question": {"repetitiveness": 0.65, "process_consistency": 0.75},
    "return request": {"repetitiveness": 0.75, "process_consistency": 0.75},
    "account access": {"repetitiveness": 0.95, "process_consistency": 0.95},
    "damaged shipment": {"repetitiveness": 0.35, "process_consistency": 0.40},
    "product question": {"repetitiveness": 0.50, "process_consistency": 0.55},
    "miscellaneous": {"repetitiveness": 0.10, "process_consistency": 0.20},
    "appointment scheduling": {"repetitiveness": 0.95, "process_consistency": 0.95},
    "insurance eligibility": {"repetitiveness": 0.72, "process_consistency": 0.68},
    "portal access": {"repetitiveness": 1.00, "process_consistency": 0.95},
    "referral status": {"repetitiveness": 0.72, "process_consistency": 0.70},
    "prescription refill request": {"repetitiveness": 0.72, "process_consistency": 0.35},
    "medical records request": {"repetitiveness": 0.72, "process_consistency": 0.82},
    "general inquiry": {"repetitiveness": 0.10, "process_consistency": 0.18},
    "order tracking": {"repetitiveness": 1.00, "process_consistency": 1.00},
    "refund status": {"repetitiveness": 0.92, "process_consistency": 0.90},
    "promotion question": {"repetitiveness": 0.32, "process_consistency": 0.30},
    "subscription change": {"repetitiveness": 0.70, "process_consistency": 0.72},
    "fraud review": {"repetitiveness": 0.18, "process_consistency": 0.22},
}


def calculate_automation_score(
    *,
    category: str,
    ticket_count: int,
    maximum_category_count: int,
    average_resolution_minutes: float,
    escalation_rate: float,
) -> float:
    """Calculate a transparent preliminary automation score from 0 to 100.

    Formula:
      30% volume: category count / largest category count
      25% repetitiveness: explicit process factor
      15% handling-time opportunity: average minutes / 90, capped at 1
      15% escalation suitability: 1 - escalation rate
      15% process consistency: explicit process factor

    The handling component represents time savings opportunity. Escalation and
    consistency components prevent complex, variable work from scoring highly
    solely because it takes a long time.
    """

    factors = PROCESS_FACTORS[category]
    volume = ticket_count / maximum_category_count if maximum_category_count else 0
    handling_time = min(max(average_resolution_minutes, 0) / 90, 1)
    escalation_suitability = 1 - min(max(escalation_rate, 0), 1)
    score = 100 * (
        0.30 * volume
        + 0.25 * factors["repetitiveness"]
        + 0.15 * handling_time
        + 0.15 * escalation_suitability
        + 0.15 * factors["process_consistency"]
    )
    return round(min(max(score, 0), 100), 2)


def analyze_support_tickets(tickets: pd.DataFrame) -> SupportSummary:
    """Aggregate a validated support ticket DataFrame using in-memory DuckDB."""

    if tickets.empty:
        raise ValueError("Cannot analyze an empty support ticket dataset")

    with duckdb.connect(":memory:") as connection:
        connection.register("tickets", tickets)
        overall = connection.execute(
            """
            SELECT
                COUNT(*) AS total_ticket_count,
                SUM(resolution_minutes) / 60.0 AS total_handling_hours,
                AVG(CAST(escalated AS INTEGER)) AS overall_escalation_rate
            FROM tickets
            """
        ).fetchone()
        category_frame = connection.execute(
            """
            SELECT
                category,
                COUNT(*) AS ticket_count,
                COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () AS category_percentage,
                AVG(resolution_minutes) AS average_resolution_minutes,
                SUM(resolution_minutes) / 60.0 AS total_handling_hours,
                AVG(CAST(escalated AS INTEGER)) AS escalation_rate
            FROM tickets
            GROUP BY category
            ORDER BY ticket_count DESC, category
            """
        ).fetchdf()
        channel_frame = connection.execute(
            """SELECT channel AS value, COUNT(*) AS ticket_count
               FROM tickets GROUP BY channel ORDER BY ticket_count DESC, channel"""
        ).fetchdf()
        tier_frame = connection.execute(
            """SELECT customer_tier AS value, COUNT(*) AS ticket_count
               FROM tickets GROUP BY customer_tier
               ORDER BY ticket_count DESC, customer_tier"""
        ).fetchdf()

    maximum_count = int(category_frame["ticket_count"].max())
    categories = []
    for row in category_frame.to_dict(orient="records"):
        row["automation_score"] = calculate_automation_score(
            category=row["category"],
            ticket_count=row["ticket_count"],
            maximum_category_count=maximum_count,
            average_resolution_minutes=row["average_resolution_minutes"],
            escalation_rate=row["escalation_rate"],
        )
        categories.append(CategoryMetrics.model_validate(row))

    return SupportSummary(
        total_ticket_count=int(overall[0]),
        total_handling_hours=round(float(overall[1]), 2),
        overall_escalation_rate=round(float(overall[2]), 6),
        by_category=categories,
        by_channel=[
            DimensionCount(value=row["value"], ticket_count=row["ticket_count"])
            for row in channel_frame.to_dict(orient="records")
        ],
        by_customer_tier=[
            DimensionCount(value=row["value"], ticket_count=row["ticket_count"])
            for row in tier_frame.to_dict(orient="records")
        ],
    )
