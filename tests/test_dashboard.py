"""Streamlit smoke test for the explicit support-audit user flow."""

from streamlit.testing.v1 import AppTest
from prismops.config import get_settings


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
