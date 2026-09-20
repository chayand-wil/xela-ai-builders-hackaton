"""Redacción de respuestas a partir de resultados calculados por src.analytics."""

from __future__ import annotations

from typing import Any

from src.agent.schemas import AgentQuery
from src.analytics.narratives import DIMENSION_LABELS, METRIC_LABELS


def _filters_line(filters: dict | None) -> str:
    if not filters:
        return "Filtros: ninguno (agregado nacional del recorte activo)."
    parts = [f"{DIMENSION_LABELS.get(key, key)}: {value}" for key, value in filters.items()]
    return "Filtros: " + ", ".join(parts)


def format_answer(
    query: AgentQuery,
    result: dict[str, Any],
    *,
    audience: str = "Público general",
    expanded: bool = False,
) -> str:
    narrative = (result.get("narrative") or "").strip()
    unit = result.get("unit")
    value = result.get("value")
    if unit == "percent" and value is not None:
        cifra = f"{float(value):.2f}%"
    elif value is None:
        cifra = "sin valor (denominador vacío o sin filas)"
    else:
        cifra = f"{int(value):,}".replace(",", " ")

    lines = [
        narrative or f"Resultado de {METRIC_LABELS.get(query.metric, query.metric)}: {cifra}.",
        _filters_line(result.get("filters") or query.filters),
    ]
    if audience == "Público general" and unit == "percent" and value is not None:
        lines.append(
            f"En palabras sencillas: equivale aproximadamente a {round(float(value))} de cada 100 inscripciones."
        )
    elif audience == "Municipalidad":
        lines.append("Esta es una señal descriptiva para priorizar revisión; por sí sola no demuestra la causa.")
    elif audience == "MINEDUC":
        lines.append("La ficha técnica completa aparece abajo con numerador, denominador, filtros y exclusiones.")
    if result.get("numerator") is not None and result.get("denominator") is not None:
        lines.append(
            f"Numerador {result['numerator']}; denominador {result['denominator']}."
        )
    if query.metric in {"ranking", "distribution"} and result.get("rows"):
        top = result["rows"][:5]
        listed = ", ".join(f"{row.get('label')} ({row.get('value')})" for row in top)
        lines.append(f"Principales grupos: {listed}.")
    if query.metric == "comparison" and result.get("rows"):
        lines.append("Se muestran los dos territorios comparados como A y B.")
    if expanded:
        lines.append(
            "Cómo leerlo: cada fila representa una inscripción de 2024, no una persona única. "
            "Promoción, no promoción y retiro excluyen Vigente e Ignorado del denominador."
        )
    if query.filters.get("graduate_status") == "Sí es graduando":
        lines.append(
            "Importante: el dato cuenta inscripciones marcadas como «Sí es graduando». "
            "No confirma que la persona haya recibido un título ni representa personas únicas."
        )
    lines.append(
        "Fuente: microdatos Educación Formal 2024 (INE), calculados con DuckDB sobre Parquet. "
        "El modelo de lenguaje no generó estas cifras."
    )
    return " ".join(lines)
