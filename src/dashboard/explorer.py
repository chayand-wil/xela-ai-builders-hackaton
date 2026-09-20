"""Explorador tabular con trazabilidad y exportación CSV."""

from __future__ import annotations

import csv
import io
from typing import Any

import streamlit as st

from src.dashboard.layout import FILTER_LABELS, render_source_and_filters, show_error

METRICS = {
    "Inscripciones": "enrollment_count",
    "Promoción": "promotion_rate",
    "No promoción": "non_promotion_rate",
    "Retiro": "withdrawal_rate",
    "Repitencia": "repetition_rate",
}


def render_explorer(svc: Any, filters: dict[str, str]) -> None:
    st.subheader("Explorador avanzado")
    st.write("Desagregue una métrica, revise numerador y denominador, y descargue el resultado reproducible.")
    metric_label = st.selectbox("Indicador", tuple(METRICS), key="expl_metric")
    group_by = st.selectbox(
        "Desagregar por", tuple(FILTER_LABELS), format_func=lambda key: FILTER_LABELS[key], key="expl_group"
    )
    try:
        result = svc.compute(METRICS[metric_label], filters, group_by=group_by, limit=500)
    except Exception as exc:  # noqa: BLE001
        show_error("No se pudo construir la tabla.", str(exc))
        return
    rows = result.get("rows", [])
    if not rows:
        st.info("No hay filas con los filtros actuales.")
        return
    st.dataframe(rows, width="stretch", hide_index=True)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    st.download_button(
        "Descargar CSV",
        buffer.getvalue().encode("utf-8-sig"),
        file_name=f"eduguate_{METRICS[metric_label]}_por_{group_by}.csv",
        mime="text/csv",
    )
    st.caption("Las tasas excluyen Vigente e Ignorado; la repitencia excluye Ignorado.")
    render_source_and_filters(filters)
