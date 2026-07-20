"""Generate reproducible customer-support datasets for all PrismOps demos."""

from __future__ import annotations

import argparse
import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

SEED = 20250720
TICKET_COUNT = 3_000

CATEGORY_CONFIG = {
    "order status": {
        "weight": 0.35,
        "resolution": (4, 18),
        "escalation_rate": 0.025,
        "descriptions": (
            "Customer requests an update for order {reference}.",
            "Customer asks when shipment {reference} will arrive.",
            "Customer cannot find tracking for order {reference}.",
        ),
    },
    "billing question": {
        "weight": 0.16,
        "resolution": (25, 85),
        "escalation_rate": 0.18,
        "descriptions": (
            "Customer questions a charge on invoice {reference}.",
            "Customer asks about payment terms for invoice {reference}.",
            "Customer reports a missing credit on invoice {reference}.",
        ),
    },
    "return request": {
        "weight": 0.13,
        "resolution": (18, 55),
        "escalation_rate": 0.12,
        "descriptions": (
            "Customer requests return authorization for order {reference}.",
            "Customer asks whether item {reference} is eligible for return.",
            "Customer needs return shipping instructions for {reference}.",
        ),
    },
    "account access": {
        "weight": 0.14,
        "resolution": (5, 22),
        "escalation_rate": 0.045,
        "descriptions": (
            "Customer cannot sign in to account {reference}.",
            "Customer requests a password reset for account {reference}.",
            "Customer reports that account {reference} is locked.",
        ),
    },
    "damaged shipment": {
        "weight": 0.07,
        "resolution": (55, 150),
        "escalation_rate": 0.46,
        "descriptions": (
            "Customer reports damaged items in shipment {reference}.",
            "Customer received crushed packaging for order {reference}.",
            "Customer requests replacement for damaged shipment {reference}.",
        ),
    },
    "product question": {
        "weight": 0.10,
        "resolution": (15, 60),
        "escalation_rate": 0.14,
        "descriptions": (
            "Customer asks about specifications for product {reference}.",
            "Customer needs compatibility guidance for product {reference}.",
            "Customer asks whether product {reference} fits their application.",
        ),
    },
    "miscellaneous": {
        "weight": 0.05,
        "resolution": (10, 120),
        "escalation_rate": 0.22,
        "descriptions": (
            "Customer submitted an uncategorized request concerning {reference}.",
            "Customer has a multi-part request without a clear owner: {reference}.",
            "Customer asks for nonstandard assistance related to {reference}.",
            "Request lacks sufficient context and references {reference}.",
            "Customer feedback requires manual review under reference {reference}.",
        ),
    },
}

CHANNELS = ("email", "phone", "web form", "chat")
CHANNEL_WEIGHTS = (0.43, 0.25, 0.22, 0.10)
CUSTOMER_TIERS = ("standard", "priority", "strategic")
CUSTOMER_TIER_WEIGHTS = (0.62, 0.27, 0.11)

HARBORPOINT_CATEGORY_CONFIG = {
    "appointment scheduling": {
        "weight": 0.26, "resolution": (8, 28), "escalation_rate": 0.08,
        "channel_weights": (0.58, 0.22, 0.12, 0.08),
        "descriptions": (
            "Administrative scheduling request for reference {reference}.",
            "Caller requests an appointment-time change under {reference}.",
            "Customer asks about available scheduling options for {reference}.",
        ),
    },
    "insurance eligibility": {
        "weight": 0.16, "resolution": (30, 85), "escalation_rate": 0.22,
        "channel_weights": (0.56, 0.16, 0.20, 0.08),
        "descriptions": (
            "Customer requests administrative eligibility verification for {reference}.",
            "Employer-plan eligibility status needs validation for {reference}.",
            "Coverage administration question references {reference}.",
        ),
    },
    "portal access": {
        "weight": 0.18, "resolution": (4, 16), "escalation_rate": 0.035,
        "channel_weights": (0.10, 0.64, 0.08, 0.18),
        "descriptions": (
            "Customer cannot access the service portal under {reference}.",
            "Portal password reset requested for {reference}.",
            "Customer reports a locked portal account under {reference}.",
        ),
    },
    "billing question": {
        "weight": 0.11, "resolution": (25, 75), "escalation_rate": 0.17,
        "channel_weights": (0.42, 0.16, 0.34, 0.08),
        "descriptions": (
            "Customer asks about an administrative statement under {reference}.",
            "Payment posting question references {reference}.",
            "Customer requests an explanation of a service charge for {reference}.",
        ),
    },
    "referral status": {
        "weight": 0.10, "resolution": (18, 55), "escalation_rate": 0.16,
        "channel_weights": (0.44, 0.24, 0.24, 0.08),
        "descriptions": (
            "Customer requests administrative referral status for {reference}.",
            "Referral routing update requested under {reference}.",
            "Customer asks whether referral paperwork was received for {reference}.",
        ),
    },
    "prescription refill request": {
        "weight": 0.09, "resolution": (35, 95), "escalation_rate": 0.48,
        "channel_weights": (0.52, 0.22, 0.18, 0.08),
        "descriptions": (
            "Administrative refill request requires licensed-team review under {reference}.",
            "Customer asks for refill-request routing under {reference}.",
            "Refill request status inquiry references {reference}; no clinical details included.",
        ),
    },
    "medical records request": {
        "weight": 0.06, "resolution": (45, 120), "escalation_rate": 0.18,
        "channel_weights": (0.16, 0.12, 0.64, 0.08),
        "descriptions": (
            "Customer requests records-release instructions under {reference}.",
            "Records request status inquiry references {reference}.",
            "Customer asks which authorization form applies to {reference}.",
        ),
    },
    "general inquiry": {
        "weight": 0.04, "resolution": (10, 90), "escalation_rate": 0.20,
        "channel_weights": (0.35, 0.20, 0.35, 0.10),
        "descriptions": (
            "Uncategorized administrative inquiry references {reference}.",
            "Customer request requires manual routing under {reference}.",
            "Multi-topic non-clinical inquiry recorded as {reference}.",
        ),
    },
}

LUMACART_CATEGORY_CONFIG = {
    "order tracking": {
        "weight": 0.30, "resolution": (3, 14), "escalation_rate": 0.02,
        "channel_weights": (0.10, 0.12, 0.18, 0.60),
        "descriptions": (
            "Shopper requests tracking status for order {reference}.",
            "Shopper asks when shipment {reference} will arrive.",
            "Tracking link question references order {reference}.",
        ),
    },
    "return request": {
        "weight": 0.18, "resolution": (15, 50), "escalation_rate": 0.12,
        "channel_weights": (0.50, 0.12, 0.25, 0.13),
        "descriptions": (
            "Shopper requests return instructions for order {reference}.",
            "Return eligibility question references {reference}.",
            "Shopper requests a return label for {reference}.",
        ),
    },
    "refund status": {
        "weight": 0.16, "resolution": (12, 38), "escalation_rate": 0.07,
        "channel_weights": (0.30, 0.12, 0.18, 0.40),
        "descriptions": (
            "Shopper requests refund status for {reference}.",
            "Refund posting timeline question references {reference}.",
            "Shopper cannot locate a processed refund under {reference}.",
        ),
    },
    "account access": {
        "weight": 0.12, "resolution": (4, 18), "escalation_rate": 0.03,
        "channel_weights": (0.14, 0.30, 0.12, 0.44),
        "descriptions": (
            "Shopper cannot access account {reference}.",
            "Password reset requested for account {reference}.",
            "Account lockout reported under {reference}.",
        ),
    },
    "promotion question": {
        "weight": 0.08, "resolution": (12, 55), "escalation_rate": 0.18,
        "channel_weights": (0.22, 0.18, 0.18, 0.42),
        "descriptions": (
            "Shopper questions campaign terms for promotion {reference}.",
            "Promotion eligibility exception references {reference}.",
            "Shopper reports a promotion did not apply under {reference}.",
        ),
    },
    "subscription change": {
        "weight": 0.07, "resolution": (15, 50), "escalation_rate": 0.14,
        "channel_weights": (0.28, 0.18, 0.20, 0.34),
        "descriptions": (
            "Shopper requests a subscription change under {reference}.",
            "Subscription pause question references {reference}.",
            "Shopper asks about subscription cancellation for {reference}.",
        ),
    },
    "fraud review": {
        "weight": 0.04, "resolution": (80, 180), "escalation_rate": 0.72,
        "channel_weights": (0.65, 0.08, 0.22, 0.05),
        "descriptions": (
            "Transaction review requires specialist approval under {reference}.",
            "Shopper responds to a manual account-security review for {reference}.",
            "High-risk order review references {reference} and requires human handling.",
        ),
    },
    "product question": {
        "weight": 0.05, "resolution": (15, 65), "escalation_rate": 0.12,
        "channel_weights": (0.20, 0.18, 0.15, 0.47),
        "descriptions": (
            "Shopper asks about product specifications for {reference}.",
            "Product compatibility question references {reference}.",
            "Shopper requests product-selection guidance under {reference}.",
        ),
    },
}

COMPANY_PROFILES = {
    "northstar-industrial-supply": {
        "seed": SEED, "categories": CATEGORY_CONFIG, "reference_prefix": "NS",
        "channels": CHANNELS, "channel_weights": CHANNEL_WEIGHTS,
        "tiers": CUSTOMER_TIERS, "tier_weights": CUSTOMER_TIER_WEIGHTS,
        "output": Path("data/demo/support_tickets.csv"),
    },
    "harborpoint-health-services": {
        "seed": 20250721, "categories": HARBORPOINT_CATEGORY_CONFIG, "reference_prefix": "HP",
        "channels": ("phone", "web portal", "email", "chat"),
        "channel_weights": (0.44, 0.25, 0.23, 0.08),
        "tiers": ("standard", "employer plan", "medicare support", "premium care"),
        "tier_weights": (0.40, 0.27, 0.23, 0.10),
        "output": Path("data/demo/harborpoint/support_tickets.csv"),
    },
    "lumacart-commerce": {
        "seed": 20250722, "categories": LUMACART_CATEGORY_CONFIG, "reference_prefix": "LC",
        "channels": ("phone", "web form", "email", "chat"),
        "channel_weights": (0.16, 0.18, 0.24, 0.42),
        "tiers": ("guest", "standard", "plus", "vip"),
        "tier_weights": (0.28, 0.43, 0.21, 0.08),
        "output": Path("data/demo/lumacart/support_tickets.csv"),
    },
}


def generate_tickets(
    count: int = TICKET_COUNT,
    seed: int | None = None,
    company_id: str = "northstar-industrial-supply",
) -> list[dict[str, object]]:
    """Return deterministic synthetic tickets for a given count and seed."""

    profile = COMPANY_PROFILES[company_id]
    rng = random.Random(profile["seed"] if seed is None else seed)
    category_config = profile["categories"]
    categories = tuple(category_config)
    weights = tuple(config["weight"] for config in category_config.values())
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    period_minutes = 181 * 24 * 60
    tickets: list[dict[str, object]] = []

    for index in range(1, count + 1):
        category = rng.choices(categories, weights=weights, k=1)[0]
        config = category_config[category]
        created_at = start + timedelta(minutes=rng.randrange(period_minutes))
        resolution_low, resolution_high = config["resolution"]
        resolution = rng.randint(resolution_low, resolution_high)
        escalated = rng.random() < config["escalation_rate"]
        if escalated:
            resolution += rng.randint(15, 60)
        reference = f"{profile['reference_prefix']}-{rng.randint(10000, 99999)}"
        description = rng.choice(config["descriptions"]).format(reference=reference)

        tickets.append(
            {
                "ticket_id": f"TKT-{index:05d}",
                "created_at": created_at.isoformat().replace("+00:00", "Z"),
                "category": category,
                "description": description,
                "resolution_minutes": resolution,
                "escalated": escalated,
                "channel": rng.choices(
                    profile["channels"],
                    weights=config.get("channel_weights", profile["channel_weights"]),
                    k=1,
                )[0],
                "customer_tier": rng.choices(
                    profile["tiers"], weights=profile["tier_weights"], k=1
                )[0],
            }
        )

    return sorted(tickets, key=lambda ticket: (ticket["created_at"], ticket["ticket_id"]))


def write_tickets(path: Path, tickets: list[dict[str, object]]) -> None:
    """Write tickets using a stable column order and CSV representation."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(tickets[0]))
        writer.writeheader()
        writer.writerows(tickets)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--company", choices=tuple(COMPANY_PROFILES), default="northstar-industrial-supply")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--count", type=int, default=TICKET_COUNT)
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()
    profile = COMPANY_PROFILES[args.company]
    output = args.output or profile["output"]
    write_tickets(output, generate_tickets(args.count, args.seed, args.company))


if __name__ == "__main__":
    main()
