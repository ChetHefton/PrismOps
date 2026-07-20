"""Tests for the three isolated, reproducible fictional demo companies."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from prismops.agents.graph import build_evidence_package
from prismops.config import get_settings
from prismops.data.companies import DEFAULT_COMPANY_ID, DEMO_COMPANIES
from prismops.data.demo import load_demo_company, load_support_process, load_support_tickets
from prismops.services import run_support_audit
from prismops.ui.session import (
    AI_REPORT_STATE_KEY,
    AI_RESULT_STATE_KEY,
    AUDIT_STATE_KEY,
    CHAT_HISTORY_STATE_KEY,
    CLARIFICATION_ANSWERS_STATE_KEY,
    REFINED_REPORT_STATE_KEY,
    SELECTED_COMPANY_STATE_KEY,
    clear_company_results,
)
from scripts.generate_support_demo import COMPANY_PROFILES, generate_tickets, write_tickets


def test_exactly_three_companies_with_northstar_default() -> None:
    assert len(DEMO_COMPANIES) == 3
    assert DEMO_COMPANIES[0].company_id == DEFAULT_COMPANY_ID
    assert [item.display_name for item in DEMO_COMPANIES] == [
        "Northstar Industrial Supply",
        "HarborPoint Health Services",
        "LumaCart Commerce",
    ]


@pytest.mark.parametrize("config", DEMO_COMPANIES, ids=lambda item: item.company_id)
def test_each_company_fixture_loads_and_has_3000_tickets(config) -> None:
    company = load_demo_company(config.company_path)
    tickets = load_support_tickets(config.tickets_path)
    process = load_support_process(config.process_path)

    assert company.id == config.company_id
    assert company.ticket_count == 3_000
    assert len(tickets) == 3_000
    assert company.demo_status == "Preloaded fictional demo"
    assert process.startswith("#")
    assert "Known limitations" in process or config.company_id == DEFAULT_COMPANY_ID


@pytest.mark.parametrize("config", DEMO_COMPANIES, ids=lambda item: item.company_id)
def test_each_committed_dataset_is_reproducible(config, tmp_path: Path) -> None:
    regenerated = tmp_path / f"{config.company_id}.csv"
    first = generate_tickets(company_id=config.company_id)
    second = generate_tickets(company_id=config.company_id)
    write_tickets(regenerated, first)

    assert first == second
    assert regenerated.read_bytes() == config.tickets_path.read_bytes()


def test_company_audits_have_distinct_metrics_and_rankings() -> None:
    audits = {
        config.company_id: run_support_audit(company_id=config.company_id)
        for config in DEMO_COMPANIES
    }
    aggregate_signatures = {
        (
            audit.summary.total_handling_hours,
            audit.summary.overall_escalation_rate,
        )
        for audit in audits.values()
    }
    top_categories = {
        audit.opportunities[0].metrics.category.value for audit in audits.values()
    }

    assert len(aggregate_signatures) == 3
    assert len(top_categories) == 3
    assert audits[DEFAULT_COMPANY_ID].opportunities[0].metrics.category.value == "order status"
    assert audits["harborpoint-health-services"].opportunities[0].metrics.category.value in {
        "appointment scheduling",
        "portal access",
    }
    harbor_ranks = {
        item.metrics.category.value: item.rank
        for item in audits["harborpoint-health-services"].opportunities
    }
    assert harbor_ranks["prescription refill request"] > harbor_ranks["appointment scheduling"]
    assert audits["lumacart-commerce"].opportunities[0].metrics.category.value == "order tracking"
    luma_ranks = {
        item.metrics.category.value: item.rank
        for item in audits["lumacart-commerce"].opportunities
    }
    assert luma_ranks["fraud review"] >= 7


def test_company_evidence_packages_do_not_leak_other_companies() -> None:
    packages = {
        config.company_id: build_evidence_package(
            run_support_audit(company_id=config.company_id)
        )
        for config in DEMO_COMPANIES
    }
    for company_id, package in packages.items():
        serialized = package.model_dump_json()
        assert package.company.id == company_id
        for other_id in packages:
            if other_id != company_id:
                assert other_id not in serialized


def test_company_change_clears_all_evidence_bearing_state() -> None:
    state = {
        SELECTED_COMPANY_STATE_KEY: "LumaCart Commerce",
        AUDIT_STATE_KEY: "old audit",
        AI_RESULT_STATE_KEY: "old evidence",
        AI_REPORT_STATE_KEY: "old report",
        CLARIFICATION_ANSWERS_STATE_KEY: ["old answer"],
        REFINED_REPORT_STATE_KEY: "old refined report",
        CHAT_HISTORY_STATE_KEY: ["old chat"],
    }
    clear_company_results(state)

    assert state == {SELECTED_COMPANY_STATE_KEY: "LumaCart Commerce"}


def test_dropdown_and_selected_metadata_update_without_upload_control(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    get_settings.cache_clear()
    app = AppTest.from_file("app.py")
    app.run(timeout=10)

    assert app.selectbox[0].value == "Northstar Industrial Supply"
    assert list(app.selectbox[0].options) == [
        "Northstar Industrial Supply",
        "HarborPoint Health Services",
        "LumaCart Commerce",
    ]

    app.selectbox[0].select("HarborPoint Health Services").run(timeout=10)
    captions = [item.value for item in app.caption]
    assert any("Healthcare services administration" in value for value in captions)
    assert any("3,000 tickets" in value for value in captions)
    assert any("under development" in value for value in captions)
    assert len(app.file_uploader) == 0
