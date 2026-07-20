"""Load and validate bundled fictional support demo inputs."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from pydantic import TypeAdapter, ValidationError

from prismops.models.support import DemoCompany, SupportTicket

DEFAULT_DEMO_COMPANY_PATH = Path("data/demo/company.json")
DEFAULT_SUPPORT_TICKETS_PATH = Path("data/demo/support_tickets.csv")
DEFAULT_SUPPORT_PROCESS_PATH = Path("data/demo/support_process.md")

REQUIRED_TICKET_COLUMNS = frozenset(
    {
        "ticket_id",
        "created_at",
        "category",
        "description",
        "resolution_minutes",
        "escalated",
        "channel",
        "customer_tier",
    }
)


class DemoDataValidationError(ValueError):
    """Raised when a bundled or supplied demo input violates its contract."""


def load_demo_company(path: Path = DEFAULT_DEMO_COMPANY_PATH) -> DemoCompany:
    """Load the fictional company metadata from JSON."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return DemoCompany.model_validate(payload)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise DemoDataValidationError(f"Invalid demo company file: {path}") from exc


def load_support_process(path: Path = DEFAULT_SUPPORT_PROCESS_PATH) -> str:
    """Load the support workflow reference document."""

    try:
        content = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise DemoDataValidationError(f"Unable to load support process: {path}") from exc
    if not content:
        raise DemoDataValidationError(f"Support process is empty: {path}")
    return content


def load_support_tickets(path: Path = DEFAULT_SUPPORT_TICKETS_PATH) -> pd.DataFrame:
    """Load CSV tickets, validate their schema and values, and normalize dtypes."""

    try:
        frame = pd.read_csv(path)
    except (OSError, pd.errors.ParserError) as exc:
        raise DemoDataValidationError(f"Unable to load support tickets: {path}") from exc

    missing = REQUIRED_TICKET_COLUMNS.difference(frame.columns)
    if missing:
        raise DemoDataValidationError(
            f"Missing required ticket columns: {', '.join(sorted(missing))}"
        )
    if frame.empty:
        raise DemoDataValidationError("Support ticket dataset must not be empty")
    if frame[list(REQUIRED_TICKET_COLUMNS)].isnull().any().any():
        raise DemoDataValidationError("Required ticket fields must not contain null values")
    if frame["ticket_id"].duplicated().any():
        raise DemoDataValidationError("ticket_id values must be unique")

    try:
        records = TypeAdapter(list[SupportTicket]).validate_python(
            frame[list(REQUIRED_TICKET_COLUMNS)].to_dict(orient="records")
        )
    except ValidationError as exc:
        raise DemoDataValidationError("One or more support tickets are invalid") from exc

    normalized = pd.DataFrame(record.model_dump(mode="python") for record in records)
    normalized["category"] = normalized["category"].map(str)
    normalized["created_at"] = pd.to_datetime(normalized["created_at"], utc=True)
    return normalized[
        [
            "ticket_id",
            "created_at",
            "category",
            "description",
            "resolution_minutes",
            "escalated",
            "channel",
            "customer_tier",
        ]
    ]
