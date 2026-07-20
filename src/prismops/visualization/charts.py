"""Reusable dark-theme Plotly figure builders for support analytics."""

from __future__ import annotations

from collections.abc import Sequence

import plotly.graph_objects as go
from plotly.colors import sample_colorscale

from prismops.models.support import CategoryMetrics

VOLUME_SCALE = [[0, "#7656d8"], [0.5, "#625bff"], [1, "#3182f6"]]
HOURS_SCALE = [[0, "#167f97"], [0.5, "#20abb9"], [1, "#36d7e7"]]
SCORE_SCALE = [[0, "#9b5cff"], [0.52, "#d05bd1"], [1, "#4f8cff"]]


def build_ticket_volume_chart(categories: Sequence[CategoryMetrics]) -> go.Figure:
    ordered = _ordered_categories(categories, "ticket_count")
    return _horizontal_bar_chart(
        ordered,
        values=[item.ticket_count for item in ordered],
        title="Ticket volume",
        subtitle="Demand by category",
        axis_title="Tickets",
        colorscale=VOLUME_SCALE,
        value_format=",d",
    )


def build_handling_hours_chart(categories: Sequence[CategoryMetrics]) -> go.Figure:
    ordered = _ordered_categories(categories, "total_handling_hours")
    return _horizontal_bar_chart(
        ordered,
        values=[item.total_handling_hours for item in ordered],
        title="Handling effort",
        subtitle="Total hours by category",
        axis_title="Hours",
        colorscale=HOURS_SCALE,
        value_format=",.1f",
    )


def build_automation_score_chart(categories: Sequence[CategoryMetrics]) -> go.Figure:
    ordered = _ordered_categories(categories, "automation_score")
    return _horizontal_bar_chart(
        ordered,
        values=[item.automation_score for item in ordered],
        title="Automation score",
        subtitle="Rules-based opportunity score",
        axis_title="Score (0–100)",
        colorscale=SCORE_SCALE,
        value_format=".1f",
        fixed_range=(0, 108),
    )


def _ordered_categories(
    categories: Sequence[CategoryMetrics], field: str
) -> list[CategoryMetrics]:
    if not categories:
        raise ValueError("At least one category is required to build a chart")
    return sorted(
        categories,
        key=lambda item: (-float(getattr(item, field)), item.category.value),
    )


def _horizontal_bar_chart(
    categories: Sequence[CategoryMetrics],
    *,
    values: list[float | int],
    title: str,
    subtitle: str,
    axis_title: str,
    colorscale: list[list[float | str]],
    value_format: str,
    fixed_range: tuple[float, float] | None = None,
) -> go.Figure:
    labels = [item.category.value.title() for item in categories]
    positions = [index / max(len(values) - 1, 1) for index in range(len(values))]
    colors = sample_colorscale(colorscale, positions)
    figure = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker={"color": colors, "line": {"color": "rgba(255,255,255,.12)", "width": 1}},
            texttemplate=f"%{{x:{value_format}}}",
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "%{y}<br>" + axis_title + f": %{{x:{value_format}}}<extra></extra>"
            ),
        )
    )
    figure.update_layout(
        title={
            "text": f"<b>{title}</b><br><span style='font-size:12px;color:#9eabc3'>{subtitle}</span>",
            "x": 0.03,
            "y": 0.97,
        },
        height=430,
        margin={"l": 118, "r": 34, "t": 72, "b": 45},
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, system-ui, sans-serif", "color": "#e8eefb", "size": 12},
        showlegend=False,
        bargap=0.32,
        hoverlabel={"bgcolor": "#151e32", "bordercolor": "#40557e", "font_color": "#f4f7ff"},
    )
    max_value = max(float(value) for value in values)
    figure.update_xaxes(
        title=axis_title,
        range=list(fixed_range) if fixed_range else [0, max_value * 1.22],
        color="#aab7cf",
        gridcolor="rgba(126,148,184,.14)",
        zeroline=False,
        showline=False,
        tickfont={"color": "#aab7cf", "size": 10},
        title_font={"color": "#aab7cf", "size": 11},
    )
    figure.update_yaxes(
        autorange="reversed",
        color="#dce5f5",
        showgrid=False,
        tickfont={"color": "#dce5f5", "size": 11},
        automargin=True,
    )
    return figure
