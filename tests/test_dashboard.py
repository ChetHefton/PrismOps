"""Streamlit smoke test for the explicit support-audit user flow."""

import pandas as pd
from streamlit.testing.v1 import AppTest

from prismops.config import get_settings
from prismops.services import run_support_audit
from prismops.ui.components.support_dashboard import render_category_analysis


def test_detailed_category_table_formats_numeric_ticket_counts(monkeypatch) -> None:
    captured = {}
    monkeypatch.setattr(
        "prismops.ui.components.support_dashboard._section_heading",
        lambda *args: None,
    )
    monkeypatch.setattr(
        "prismops.ui.components.support_dashboard.st.caption",
        lambda *args: None,
    )
    monkeypatch.setattr(
        "prismops.ui.components.support_dashboard.st.dataframe",
        lambda frame, **kwargs: captured.update(frame=frame, **kwargs),
    )

    audit = run_support_audit()
    render_category_analysis(audit)

    frame = captured["frame"]
    ticket_config = captured["column_config"]["Ticket count"]
    assert frame["Ticket count"].tolist() == [
        item.ticket_count for item in audit.summary.by_category
    ]
    assert pd.api.types.is_integer_dtype(frame["Ticket count"])
    assert ticket_config["type_config"]["format"] == "%,d"


def test_dashboard_runs_audit_without_rendering_errors(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    get_settings.cache_clear()
    app = AppTest.from_file("app.py")
    app.run(timeout=10)

    assert not app.exception
    assert app.selectbox[0].value == "Northstar Industrial Supply"
    assert app.button[0].label == "Run Support Audit"

    app.button[0].click().run(timeout=10)

    assert not app.exception
    headings = [item.value for item in app.subheader]
    expected_order = [
        "AI Intelligence",
        "Executive overview",
        "Category visualizations",
        "Automation opportunity ranking",
        "Detailed category table",
        "Process documentation",
        "Scoring methodology",
        "Grounded Audit Assistant",
    ]
    assert [headings.index(value) for value in expected_order] == sorted(
        headings.index(value) for value in expected_order
    )
    assert all(button.label != "Generate AI Recommendations" for button in app.button)
    assert len(app.chat_input) == 0


def test_ai_control_is_available_with_configured_key(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "placeholder-key")
    get_settings.cache_clear()
    app = AppTest.from_file("app.py")
    app.run(timeout=10)
    app.button[0].click().run(timeout=10)

    assert not app.exception
    assert "Generate AI Recommendations" in [button.label for button in app.button]
    assert len(app.chat_input) == 0
