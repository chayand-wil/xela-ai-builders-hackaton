"""Tab Territorio: departamento → barras municipales y narrativa del backend."""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.dashboard.charts import bars_from_result
from src.dashboard.filters import TODOS, as_str_list, normalize_options
from src.dashboard.layout import (
    extract_rows,
    format_kpi_value,
    format_number,
    render_source_and_filters,
    result_get,
    row_label,
    row_value,
    show_empty,
    show_error,
)


def render_territory(svc: Any, filters: dict[str, str], options: dict[str, Any]) -> None:
    st.subheader("Exploración territorial")
    st.write(
        "Elija un departamento para ver cómo se reparte la matrícula entre municipios. "
        "Los filtros del menú izquierdo siguen aplicándose (nivel, sector, etc.)."
    )

    opts = normalize_options(options)
    departments = as_str_list(opts.get("department"))
    sidebar_dept = filters.get("department")

    if not departments and not sidebar_dept:
        show_error("No hay lista de departamentos en `filter_options()`.")
        return

    default_index = 0
    if sidebar_dept and sidebar_dept in departments:
        default_index = departments.index(sidebar_dept)

    selected = st.selectbox(
        "Departamento a explorar",
        options=departments or [sidebar_dept],
        index=min(default_index, max(len(departments) - 1, 0)) if departments else 0,
        help="Si ya filtró un departamento en la barra lateral, aparece preseleccionado.",
    )
    if not selected or selected == TODOS:
        st.info("Seleccione un departamento para ver la desagregación municipal.")
        return

    local_filters = dict(filters)
    local_filters["department"] = selected
    local_filters.pop("municipality", None)

    if selected == "Guatemala":
        st.caption("Control de calidad: el departamento de Guatemala debe mostrar **17** municipios.")

    try:
        with st.spinner("Consultando municipios…"):
            enrollment = svc.compute(
                "enrollment_count",
                local_filters,
                group_by="municipality",
                limit=40,
            )
            withdrawal = svc.compute(
                "withdrawal_rate",
                local_filters,
                group_by="municipality",
                limit=15,
            )
            kpis = svc.kpis(local_filters) if hasattr(svc, "kpis") else None
    except Exception as exc:  # noqa: BLE001
        show_error("No se pudo calcular la vista territorial.", str(exc))
        return

    enroll_rows = extract_rows(enrollment)
    if not enroll_rows:
        show_empty(f"No hay inscripciones municipales para {selected} con los filtros actuales.")
        return

    if kpis is not None:
        enroll_kpi = None
        data = kpis if isinstance(kpis, dict) else None
        if data:
            enroll_kpi = data.get("enrollment_count")
        if enroll_kpi is None and hasattr(kpis, "enrollment_count"):
            enroll_kpi = kpis.enrollment_count
        if enroll_kpi is not None:
            st.metric(
                f"Inscripciones en {selected}",
                format_kpi_value(enroll_kpi),
                help="Conteo de inscripciones, no personas únicas.",
            )

    n_muni = len(enroll_rows)
    st.caption(f"Municipios con datos en esta consulta: **{n_muni}**.")

    col_left, col_right = st.columns(2)
    with col_left:
        st.plotly_chart(
            bars_from_result(
                enrollment,
                title=f"Inscripciones municipales · {selected}",
                horizontal=True,
                value_axis_title="Inscripciones",
            ),
            width="stretch",
        )
        narrative = result_get(enrollment, "narrative", default=None)
        if narrative:
            st.markdown(str(narrative))
        else:
            top = max(enroll_rows, key=lambda row: row_value(row) or 0)
            st.markdown(
                f"En **{selected}**, el municipio con más inscripciones en esta vista es "
                f"**{row_label(top)}** ({format_number(row_value(top))} registros). "
                f"Eso no significa peor o mejor aprendizaje: solo indica volumen."
            )

    with col_right:
        st.plotly_chart(
            bars_from_result(
                withdrawal,
                title=f"Tasa de retiro por municipio (hasta 15) · {selected}",
                horizontal=True,
                value_axis_title="Tasa (capa analítica)",
                color="#922B21",
            ),
            width="stretch",
        )
        wd_narrative = result_get(withdrawal, "narrative", default=None)
        if wd_narrative:
            st.markdown(str(wd_narrative))
        else:
            st.markdown(
                "La tasa de retiro **ya viene calculada** (Retirado + Retirado definitivo sobre "
                "resultado conocido). Compare municipios con pocos casos con cautela: un porcentaje "
                "alto puede salir de un denominador pequeño."
            )

    render_source_and_filters(local_filters)
