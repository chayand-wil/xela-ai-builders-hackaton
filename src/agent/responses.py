"""Redacción de respuestas a partir de resultados calculados por src.analytics."""

from __future__ import annotations

from typing import Any

from src.agent.schemas import AgentQuery


def _filters_line(filters: dict | None) -> str:
    if not filters:
        return "Filtros: ninguno (agregado nacional del recorte activo)."
    parts = [f"{key}={value}" for key, value in filters.items()]
    return "Filtros: " + ", ".join(parts)


def format_answer(query: AgentQuery, result: dict[str, Any]) -> str:
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
        narrative or f"Resultado de {query.metric}: {cifra}.",
        _filters_line(result.get("filters") or query.filters),
    ]
    if result.get("numerator") is not None and result.get("denominator") is not None:
        lines.append(
            f"Numerador {result['numerator']}; denominador {result['denominator']}."
        )
    if query.metric in {"ranking", "distribution"} and result.get("rows"):
        top = result["rows"][:5]
        listed = ", ".join(f"{row.get('label')} ({row.get('value')})" for row in top)
        lines.append(f"Principales grupos: {listed}.")
    if query.metric == "comparison" and result.get("rows"):
        lines.append("Los dos conjuntos comparados están en rows (A y B).")
    lines.append(
        "Fuente: microdatos Educación Formal 2024 (INE), calculados con DuckDB sobre Parquet. "
        "El modelo de lenguaje no generó estas cifras."
    )
    return " ".join(lines)
