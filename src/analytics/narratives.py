"""Textos deterministas en español a partir de cifras ya calculadas."""

from __future__ import annotations

from typing import Any

from src.analytics.indicators import IGNORADO_LABEL, VIGENTE_OUTCOME

DIMENSION_LABELS = {
    "department": "departamento",
    "municipality": "municipio",
    "level": "nivel educativo",
    "sector": "sector",
    "area": "área",
    "sex": "sexo",
    "ethnicity": "pueblo de pertenencia",
    "shift": "jornada",
    "study_plan": "plan de estudios",
    "outcome": "resultado",
}

METRIC_LABELS = {
    "enrollment_count": "inscripciones",
    "promotion_rate": "tasa de promoción",
    "non_promotion_rate": "tasa de no promoción",
    "withdrawal_rate": "tasa de retiro",
    "repetition_rate": "tasa de repitencia",
}


def _fmt_int(value: int | None) -> str:
    if value is None:
        return "n/d"
    return f"{value:,}".replace(",", " ")


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "n/d"
    return f"{value:.2f}%"


def _filters_es(filters: dict | None) -> str:
    if not filters:
        return "sin filtros territoriales ni de dimensión"
    parts = [f"{DIMENSION_LABELS.get(key, key)}: {value}" for key, value in filters.items()]
    return ", ".join(parts)


def describe_enrollment(value: int, filters: dict | None) -> str:
    return (
        f"Hay {_fmt_int(value)} inscripciones en el ciclo 2024 "
        f"({_filters_es(filters)}). Cada fila es una inscripción, no una persona única."
    )


def describe_rate(name: str, value: float | None, numerator: int, denominator: int, filters: dict | None) -> str:
    if denominator == 0:
        return (
            f"No hay registros con resultado terminal conocido para calcular {name} "
            f"({_filters_es(filters)}). Vigente e Ignorado no entran en el denominador."
        )
    return (
        f"{name}: {_fmt_pct(value)} "
        f"({_fmt_int(numerator)} de {_fmt_int(denominator)} inscripciones con resultado terminal). "
        f"El denominador es Promovido + No promovido + Retirado + Retirado definitivo. "
        f"Filtros: {_filters_es(filters)}."
    )


def describe_distribution(dimension: str, rows: list[dict], filters: dict | None) -> str:
    dimension_label = DIMENSION_LABELS.get(dimension, dimension)
    if not rows:
        return f"No hay inscripciones para distribuir por {dimension_label} ({_filters_es(filters)})."
    top = rows[0]
    return (
        f"Distribución de inscripciones por {dimension_label} ({_filters_es(filters)}). "
        f"El grupo con más inscripciones es {top.get('label')} ({_fmt_int(int(top.get('value') or 0))})."
    )


def describe_ranking(dimension: str, rows: list[dict], unit: str, filters: dict | None) -> str:
    dimension_label = DIMENSION_LABELS.get(dimension, dimension)
    if not rows:
        return f"No hay grupos para ordenar por {dimension_label} ({_filters_es(filters)})."
    top = rows[0]
    if unit == "percent" and top.get("value") is not None:
        shown = _fmt_pct(float(top["value"]))
    else:
        shown = _fmt_int(int(top.get("value") or 0))
    return (
        f"El primer lugar por {dimension_label} es {top.get('label')} con {shown} "
        f"({_filters_es(filters)})."
    )


def describe_comparison(left: dict[str, Any], right: dict[str, Any], metric: str) -> str:
    metric_label = METRIC_LABELS.get(metric, metric)
    left_v = left.get("value")
    right_v = right.get("value")
    if left_v is None or right_v is None:
        return f"No se pudo comparar {metric_label}: falta denominador en uno de los conjuntos."
    diff = float(right_v) - float(left_v)
    unit = left.get("unit") or right.get("unit")
    if unit == "percent":
        diff_txt = f"{diff:+.2f} puntos porcentuales"
        left_txt = _fmt_pct(float(left_v))
        right_txt = _fmt_pct(float(right_v))
    else:
        diff_txt = f"{diff:+,.0f}".replace(",", " ")
        left_txt = _fmt_int(int(left_v))
        right_txt = _fmt_int(int(right_v))
    return (
        f"Comparación de {metric_label}: conjunto A = {left_txt} ({_filters_es(left.get('filters'))}); "
        f"conjunto B = {right_txt} ({_filters_es(right.get('filters'))}). "
        f"Diferencia B − A: {diff_txt}."
    )


def describe_kpis(kpis: dict[str, Any]) -> str:
    enrollment = kpis["enrollment_count"]["value"]
    promo = kpis["promotion_rate"]["value"]
    vigente = kpis["vigente_count"]
    ignorado = kpis["ignorado_count"]
    return (
        f"{_fmt_int(int(enrollment))} inscripciones. "
        f"Promoción {_fmt_pct(promo)}, no promoción {_fmt_pct(kpis['non_promotion_rate']['value'])}, "
        f"retiro {_fmt_pct(kpis['withdrawal_rate']['value'])}. "
        f"{VIGENTE_OUTCOME}: {_fmt_int(int(vigente))}. {IGNORADO_LABEL}: {_fmt_int(int(ignorado))}."
    )
