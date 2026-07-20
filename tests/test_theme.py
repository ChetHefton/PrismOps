"""Tests for centralized PrismOps theme application."""

from prismops.ui import theme


def test_theme_is_applied_through_one_central_function(monkeypatch) -> None:
    calls = []

    def capture(markup, *, unsafe_allow_html=False):
        calls.append((markup, unsafe_allow_html))

    monkeypatch.setattr(theme.st, "markdown", capture)
    theme.apply_prismops_theme()

    assert len(calls) == 1
    assert calls[0][1] is True
