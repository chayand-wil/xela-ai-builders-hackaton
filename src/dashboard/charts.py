"""Figuras Plotly a partir de agregados ya calculados (nunca tasas locales)."""

from __future__ import annotations

from typing import Any

import plotly.graph_objects as go

from src.dashboard.layout import extract_rows, row_label, row_value

BAR_COLOR = "#1B4F72"


def _empty_figure(title: str, message: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=title,
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": 14, "color": "#5D6D7E"},
            }
        ],
        margin={"l": 24, "r": 16, "t": 48, "b": 24},
        height=360,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def bars_from_result(
    result: Any,
    *,
    title: str,
    horizontal: bool = False,
    value_axis_title: str = "Inscripciones",
    color: str = BAR_COLOR,
) -> go.Figure:
    rows = extract_rows(result)
    labels: list[str] = []
    values: list[float] = []
    for row in rows:
        value = row_value(row)
        if value is None:
            continue
        labels.append(row_label(row))
        values.append(value)
    if not labels:
        return _empty_figure(title, "Sin datos para esta gráfica con los filtros actuales.")

    if horizontal:
        fig = go.Figure(
            go.Bar(
                x=values,
                y=labels,
                orientation="h",
                marker_color=color,
                hovertemplate="%{y}: %{x}<extra></extra>",
            )
        )
        fig.update_layout(yaxis={"autorange": "reversed"})
        fig.update_xaxes(title=value_axis_title)
        fig.update_yaxes(title="")
    else:
        fig = go.Figure(
            go.Bar(
                x=labels,
                y=values,
                marker_color=color,
                hovertemplate="%{x}: %{y}<extra></extra>",
            )
        )
        fig.update_xaxes(title="")
        fig.update_yaxes(title=value_axis_title)

    fig.update_layout(
        title=title,
        margin={"l": 24, "r": 16, "t": 56, "b": 48},
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Source Sans Pro, sans-serif"},
    )
    return fig


def donut_from_result(result: Any, *, title: str) -> go.Figure:
    rows = extract_rows(result)
    labels: list[str] = []
    values: list[float] = []
    for row in rows:
        value = row_value(row)
        if value is None:
            continue
        labels.append(row_label(row))
        values.append(value)
    if not labels:
        return _empty_figure(title, "Sin datos para esta gráfica con los filtros actuales.")
    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.45,
            hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
            marker={"colors": ["#1E8449", "#5D6D7E", "#CA6F1E", "#922B21", "#1B4F72", "#AF7AC5"]},
        )
    )
    fig.update_layout(
        title=title,
        margin={"l": 16, "r": 16, "t": 56, "b": 16},
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        legend={"orientation": "h", "y": -0.08},
    )
    return fig
