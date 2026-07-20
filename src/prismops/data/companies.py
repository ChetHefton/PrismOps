"""Registry of the preloaded fictional support demo companies."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DemoCompanyConfig:
    company_id: str
    display_name: str
    company_path: Path
    tickets_path: Path
    process_path: Path


DEFAULT_COMPANY_ID = "northstar-industrial-supply"

DEMO_COMPANIES = (
    DemoCompanyConfig(
        company_id=DEFAULT_COMPANY_ID,
        display_name="Northstar Industrial Supply",
        company_path=Path("data/demo/company.json"),
        tickets_path=Path("data/demo/support_tickets.csv"),
        process_path=Path("data/demo/support_process.md"),
    ),
    DemoCompanyConfig(
        company_id="harborpoint-health-services",
        display_name="HarborPoint Health Services",
        company_path=Path("data/demo/harborpoint/company.json"),
        tickets_path=Path("data/demo/harborpoint/support_tickets.csv"),
        process_path=Path("data/demo/harborpoint/support_process.md"),
    ),
    DemoCompanyConfig(
        company_id="lumacart-commerce",
        display_name="LumaCart Commerce",
        company_path=Path("data/demo/lumacart/company.json"),
        tickets_path=Path("data/demo/lumacart/support_tickets.csv"),
        process_path=Path("data/demo/lumacart/support_process.md"),
    ),
)

COMPANY_BY_ID = {company.company_id: company for company in DEMO_COMPANIES}


def get_demo_company_config(company_id: str = DEFAULT_COMPANY_ID) -> DemoCompanyConfig:
    try:
        return COMPANY_BY_ID[company_id]
    except KeyError as exc:
        raise ValueError(f"Unknown demo company: {company_id}") from exc
