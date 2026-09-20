"""Comparador explícito de dos territorios."""

from __future__ import annotations

from typing import Any

import plotly.graph_objects as go
import streamlit as st

from src.dashboard.filters import as_str_list, municipality_choices, normalize_options
from src.dashboard.layout import format_number, render_source_and_filters, show_error

METRICS = {
    "Inscripciones": "enrollment_count",
    "Promoción": "promotion_rate",
    "No promoción": "non_promotion_rate",
    "Retiro": "withdrawal_rate",
    "Repitencia": "repetition_rate",
}


def _territory(label: str, options: dict[str, Any], key: str) -> dict[str, str]:
    departments = as_str_list(options.get("department"))
    department = st.selectbox(f"Departamento {label}", departments, key=f"cmp_dept_{key}")
    municipalities = municipality_choices(options, department)
    municipality = st.selectbox(
        f"Municipio {label} (opcional)", ["Todo el departamento", *municipalities], key=f"cmp_muni_{key}"
    )
    result = {"department": department}
    if municipality != "Todo el departamento":
        result["municipality"] = municipality
    return result


def render_compare(svc: Any, filters: dict[str, str], options: dict[str, Any]) -> None:
    st.subheader("Comparador territorial")
    st.write("Compare la misma métrica entre dos territorios. Una diferencia observada no demuestra una causa.")
    normalized = normalize_options(options)
    col_a, col_b = st.columns(2)
    with col_a:
        left = _territory("A", normalized, "a")
    with col_b:
        right = _territory("B", normalized, "b")
    metric_label = st.selectbox("Métrica", tuple(METRICS))
    metric = METRICS[metric_label]
    common = {k: v for k, v in filters.items() if k not in {"department", "municipality"}}
    left = {**common, **left}
    right = {**common, **right}
    try:
        result = svc.compute("comparison", left, compare_filters=right, rank_metric=metric)
    except Exception as exc:  # noqa: BLE001
        show_error("No se pudo completar la comparación.", str(exc))
        return
    rows = result.get("rows", [])
    values = [row.get("value") for row in rows]
    suffix = "%" if result.get("unit") == "percent" else ""
    fig = go.Figure(
        go.Bar(
            x=["A", "B"],
            y=values,
            marker_color=["#1B4F72", "#148F77"],
            text=[f"{format_number(v)}{suffix}" for v in values],
        )
    )
    fig.update_layout(title=metric_label, yaxis_title=metric_label, height=380)
    st.plotly_chart(fig, width="stretch")
    cards = st.columns(3)
    cards[0].metric("Territorio A", f"{format_number(values[0])}{suffix}" if rows else "—")
    cards[1].metric("Territorio B", f"{format_number(values[1])}{suffix}" if len(rows) > 1 else "—")
    cards[2].metric("Diferencia B − A", f"{format_number(result.get('value'))}{suffix}")
    st.markdown(result.get("narrative", ""))
    if metric != "enrollment_count":
        st.warning("Compare también los denominadores: una tasa alta con pocos casos requiere cautela.")
        st.dataframe(rows, width="stretch", hide_index=True)
    render_source_and_filters(common)
