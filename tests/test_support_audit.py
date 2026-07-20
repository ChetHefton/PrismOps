"""Integration tests for the dashboard-facing support audit facade."""

from prismops.services import run_support_audit


def test_audit_service_returns_complete_ui_contract() -> None:
    audit = run_support_audit()

    assert audit.company.name == "Northstar Industrial Supply"
    assert audit.summary.total_ticket_count == 3_000
    assert audit.highest_volume_category.value == "order status"
    assert audit.highest_automation_category == audit.opportunities[0].metrics.category
    assert len(audit.opportunities) == len(audit.summary.by_category) == 7
    assert [item.rank for item in audit.opportunities] == list(range(1, 8))
    assert "## Order status" in audit.process_documentation
