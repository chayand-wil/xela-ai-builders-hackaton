"""Tab Panorama nacional: KPIs, cuatro Plotly y textos para público no técnico."""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.dashboard.charts import bars_from_result, donut_from_result
from src.dashboard.layout import (
    extract_rows,
    format_number,
    normalize_kpis,
    render_kpi_row,
    render_source_and_filters,
    result_get,
    row_label,
    row_value,
    show_empty,
    show_error,
)


def _narrative_or(result: Any, fallback: str) -> str:
    text = result_get(result, "narrative", default=None)
    if text:
        return str(text)
    return fallback


def _has_volume(kpis: dict[str, Any]) -> bool:
    enroll = kpis.get("enrollment_count")
    value = result_get(enroll, "value", "numerator", default=None)
    try:
        return value is not None and float(value) > 0
    except (TypeError, ValueError):
        return enroll is not None


def _top_row_sentence(result: Any, *, entity: str, unit_phrase: str) -> str:
    rows = extract_rows(result)
    scored: list[tuple[str, float]] = []
    for row in rows:
        value = row_value(row)
        if value is None:
            continue
        scored.append((row_label(row), value))
    if not scored:
        return "No hay suficientes agregados para redactar una lectura."
    scored.sort(key=lambda item: item[1], reverse=True)
    label, value = scored[0]
    return (
        f"El {entity} con mayor volumen en esta vista es **{label}** "
        f"({format_number(value)} {unit_phrase}). Eso describe tamaño, no “mejor” ni “peor” resultado."
    )


def render_overview(svc: Any, filters: dict[str, str]) -> None:
    st.subheader("Panorama nacional")
    st.write(
        "Resumen del ciclo 2024 con los filtros del menú izquierdo. "
        "Las tasas las calcula la capa analítica; aquí solo se muestran."
    )

    try:
        with st.spinner("Calculando indicadores…"):
            kpis_raw = svc.kpis(filters) if hasattr(svc, "kpis") else None
            if kpis_raw is None:
                kpis_raw = {
                    "enrollment_count": svc.compute("enrollment_count", filters),
                    "promotion_rate": svc.compute("promotion_rate", filters),
                    "non_promotion_rate": svc.compute("non_promotion_rate", filters),
                    "withdrawal_rate": svc.compute("withdrawal_rate", filters),
                }
            dist_level = svc.distribution("level", filters)
            dist_outcome = svc.distribution("outcome", filters)
            dist_sector = svc.distribution("sector", filters)
            ranking = svc.compute(
                "enrollment_count",
                filters,
                group_by="department",
                limit=22,
            )
    except Exception as exc:  # noqa: BLE001 — mostrar fallo de analítica al usuario
        show_error("No se pudieron calcular los indicadores de panorama.", str(exc))
        return

    kpis = normalize_kpis(kpis_raw)
    if not kpis:
        show_error("La capa analítica no devolvió los cuatro indicadores esperados.")
        return

    render_kpi_row(kpis)
    render_source_and_filters(filters)

    if not _has_volume(kpis):
        show_empty()
        return

    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(
            bars_from_result(
                dist_level,
                title="Inscripciones por nivel educativo",
                value_axis_title="Inscripciones",
            ),
            width="stretch",
        )
        st.markdown(
            _narrative_or(
                dist_level,
                _top_row_sentence(dist_level, entity="nivel", unit_phrase="inscripciones")
                + " Primaria suele concentrar la mayor parte de la matrícula del país.",
            )
        )
        st.caption("Lectura: volumen de inscripciones, no tasa de éxito.")

    with col_b:
        st.plotly_chart(
            donut_from_result(dist_outcome, title="Composición del resultado del ciclo"),
            width="stretch",
        )
        st.markdown(
            _narrative_or(
                dist_outcome,
                "Esta gráfica muestra **todas** las categorías de resultado, incluidas Vigente e Ignorado. "
                "Las tasas de las tarjetas de arriba **no** usan Vigente ni Ignorado en el denominador.",
            )
        )
        st.caption("No interprete el donut como las mismas tasas de las tarjetas.")

    col_c, col_d = st.columns(2)
    with col_c:
        st.plotly_chart(
            bars_from_result(
                dist_sector,
                title="Inscripciones por sector",
                value_axis_title="Inscripciones",
                color="#148F77",
            ),
            width="stretch",
        )
        st.markdown(
            _narrative_or(
                dist_sector,
                _top_row_sentence(dist_sector, entity="sector", unit_phrase="inscripciones")
                + " El sector público suele agrupar la mayoría de las inscripciones.",
            )
        )
        st.caption("Sector describe quién administra el servicio, no la calidad educativa.")

    with col_d:
        st.plotly_chart(
            bars_from_result(
                ranking,
                title="Inscripciones por departamento",
                horizontal=True,
                value_axis_title="Inscripciones",
            ),
            width="stretch",
        )
        st.markdown(
            _narrative_or(
                ranking,
                _top_row_sentence(ranking, entity="departamento", unit_phrase="inscripciones")
                + " Un departamento más poblado en matrícula no implica peor o mejor retiro.",
            )
        )
        st.caption("Ranking de volumen. Para tasas, use Territorio o Preguntar a los datos.")

    render_source_and_filters(filters)
