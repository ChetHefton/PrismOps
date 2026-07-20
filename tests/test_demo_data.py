"""Tests for loading and validating the Northstar demo inputs."""

from pathlib import Path

import pandas as pd
import pytest

from prismops.data.demo import (
    REQUIRED_TICKET_COLUMNS,
    DemoDataValidationError,
    load_demo_company,
    load_support_process,
    load_support_tickets,
)


def test_demo_files_load_successfully() -> None:
    company = load_demo_company()
    tickets = load_support_tickets()
    process = load_support_process()

    assert company.name == "Northstar Industrial Supply"
    assert len(tickets) == 3_000
    assert REQUIRED_TICKET_COLUMNS.issubset(tickets.columns)
    assert "## Damaged shipment" in process


def test_required_csv_columns_are_validated(tmp_path: Path) -> None:
    invalid_path = tmp_path / "tickets.csv"
    pd.DataFrame({"ticket_id": ["TKT-1"]}).to_csv(invalid_path, index=False)

    with pytest.raises(DemoDataValidationError, match="Missing required ticket columns"):
        load_support_tickets(invalid_path)
