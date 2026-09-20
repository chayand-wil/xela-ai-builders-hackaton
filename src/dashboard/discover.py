"""Hallazgos descriptivos calculados, sin atribuir causalidad."""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.dashboard.layout import format_number, render_source_and_filters, show_error


def _top(result: dict[str, Any]) -> dict[str, Any] | None:
    rows = result.get("rows", [])
    return rows[0] if rows else None


def render_discover(svc: Any, filters: dict[str, str]) -> None:
    st.subheader("Datos que quizá no conocías")
    st.write("Hallazgos descriptivos con los filtros actuales. Son señales para explorar, no explicaciones causales.")
    try:
        level = _top(svc.compute("enrollment_count", filters, group_by="level", limit=1))
        sector = _top(svc.compute("enrollment_count", filters, group_by="sector", limit=1))
        withdrawal = _top(
            svc.compute("ranking", filters, group_by="department", limit=1, rank_metric="withdrawal_rate")
        )
    except Exception as exc:  # noqa: BLE001
        show_error("No se pudieron calcular los hallazgos.", str(exc))
        return
    cards = st.columns(3)
    with cards[0]:
        st.metric("Nivel con más inscripciones", level.get("label", "—") if level else "—")
        if level:
            st.caption(f"{format_number(level.get('value'))} inscripciones.")
    with cards[1]:
        st.metric("Sector con más inscripciones", sector.get("label", "—") if sector else "—")
        if sector:
            st.caption(f"{format_number(sector.get('value'))} inscripciones.")
    with cards[2]:
        st.metric("Mayor tasa de retiro", withdrawal.get("label", "—") if withdrawal else "—")
        if withdrawal:
            st.caption(
                f"{float(withdrawal.get('value')):.1f}% · {format_number(withdrawal.get('numerator'))} de "
                f"{format_number(withdrawal.get('denominator'))} resultados conocidos."
            )
    st.info("Una diferencia territorial puede relacionarse con factores que este dataset no contiene.")
    render_source_and_filters(filters)
