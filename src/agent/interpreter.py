"""Intérprete: OpenAI JSON estructurado si hay clave; si no, modo demo por palabras clave."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from dotenv import load_dotenv

from src.agent.guardrails import fold
from src.agent.schemas import AgentQuery
from src.analytics.queries import FILTER_KEYS
from src.ingestion.catalogs import (
    AREA_MAP,
    DEPARTAMENTOS_MAP,
    JORNADA_MAP,
    NIVEL_MAP,
    PLAN_EST_MAP,
    PUEBLO_MAP,
    RESULTADO_MAP,
    SECTOR_MAP,
    SEXO_MAP,
)

SYSTEM_PROMPT = """Eres el intérprete de EduGuate IA (Educación Formal Guatemala 2024).
Traduce la pregunta a un JSON de consulta. NO calcules cifras y NO escribas SQL.

metric debe ser una de:
enrollment_count, promotion_rate, non_promotion_rate, withdrawal_rate,
repetition_rate, distribution, ranking, comparison.

filters y compare_filters usan estas claves en inglés:
department, municipality, level, sector, area, sex, ethnicity, shift, study_plan, outcome.

Valores canónicos:
- department: nombres oficiales (Guatemala, Quetzaltenango, Alta Verapaz, ...)
- level: Preprimaria, Primaria, Básico, Diversificado, Primaria de adultos, Ignorado
- sector: Público, Privado, Municipal, Cooperativa
- area: Urbana, Rural, Ignorado
- sex: Hombre, Mujer, Ignorado
- outcome: Promovido, Vigente, Retirado, Retirado definitivo, No promovido, Ignorado
- ethnicity: Maya, Garífuna, Xinka, Afrodescendiente/Creole/Afromestizo, Ladino/Mestizo, Extranjero, Ignorado
- shift: Matutina, Vespertina, Nocturna, Doble, Intermedia, Ignorado
- study_plan: Diario, Fin de semana, Virtual a distancia, Semipresencial, Mixto

Reglas:
- Una fila es una inscripción, no una persona única.
- ranking: group_by obligatorio; usa rank_metric si rankean una tasa.
- comparison: filters = conjunto A, compare_filters = conjunto B; rank_metric = métrica comparada.
- distribution: group_by obligatorio.
- Retiro combina Retirado + Retirado definitivo (withdrawal_rate).
- Si piden el departamento con más inscripciones: ranking, group_by=department, rank_metric=enrollment_count.
"""

load_dotenv()


def _catalog_pairs(values: list[str]) -> list[tuple[str, str]]:
    return sorted(((fold(value), value) for value in values), key=lambda item: -len(item[0]))


_VALUE_LOOKUPS: dict[str, list[tuple[str, str]]] = {
    "department": _catalog_pairs(list(DEPARTAMENTOS_MAP.values())),
    "level": _catalog_pairs(list(NIVEL_MAP.values())),
    "sector": _catalog_pairs(list(SECTOR_MAP.values())),
    "area": _catalog_pairs(list(AREA_MAP.values())),
    "sex": _catalog_pairs(list(SEXO_MAP.values())),
    "ethnicity": _catalog_pairs(list(PUEBLO_MAP.values())),
    "shift": _catalog_pairs(list(JORNADA_MAP.values())),
    "study_plan": _catalog_pairs(list(PLAN_EST_MAP.values())),
    "outcome": _catalog_pairs(list(RESULTADO_MAP.values())),
}


def _find_values(text: str, key: str) -> list[str]:
    found: list[str] = []
    for needle, canonical in _VALUE_LOOKUPS[key]:
        if needle and needle in text:
            found.append(canonical)
    return found


def interpret_demo(question: str, previous_query: AgentQuery | None = None) -> AgentQuery:
    """Modo demo: cubre el banco de preguntas del plan sin llamar a la API."""
    text = fold(question)
    if previous_query is not None:
        if re.search(r"\b(mas detalle|más detalle|explica|facil|fácil|denominador|metodologia|metodología)\b", text):
            return previous_query
        followup_groups = {
            "municip": "municipality",
            "departamento": "department",
            "sector": "sector",
            "nivel": "level",
            "area": "area",
            "sexo": "sex",
            "jornada": "shift",
        }
        followup_text = text.lstrip("¿¡ ")
        if followup_text.startswith(("y ", "ahora ", "tambien ", "también ")):
            for word, group in followup_groups.items():
                if word in text:
                    metric = previous_query.metric
                    rank_metric = previous_query.rank_metric
                    if metric not in {"distribution", "ranking"}:
                        rank_metric = metric
                        metric = "ranking" if "mayor" in text or "mas" in text else "distribution"
                    return previous_query.model_copy(
                        update={"metric": metric, "group_by": group, "rank_metric": rank_metric}
                    )
    departments = _find_values(text, "department")
    levels = _find_values(text, "level")
    sectors = _find_values(text, "sector")
    areas = _find_values(text, "area")
    sexes = _find_values(text, "sex")

    filters: dict[str, Any] = {}
    if levels:
        filters["level"] = levels[0]
    if sectors:
        filters["sector"] = sectors[0]
    if sexes:
        filters["sex"] = sexes[0]

    wants_distribution = bool(re.search(r"distrib", text))
    wants_compare = bool(re.search(r"compara", text)) or (" o " in text and len(areas) >= 2)
    wants_rank = bool(re.search(r"\b(mas|mayor|ranking|primero|top)\b", text)) and not wants_compare
    wants_withdrawal = bool(re.search(r"retir", text))
    wants_non_promo = bool(re.search(r"no promov", text))
    wants_promo = bool(re.search(r"promoc", text)) and not wants_non_promo
    wants_repeat = bool(re.search(r"repiten", text))
    wants_count = bool(re.search(r"cuant", text) or re.search(r"inscripcion", text))

    requested_group = None
    group_words = {
        "municip": "municipality",
        "departamento": "department",
        "sector": "sector",
        "nivel": "level",
        "area": "area",
        "sexo": "sex",
        "jornada": "shift",
        "resultado": "outcome",
    }
    if " por " in text or "graf" in text or "muestra" in text:
        for word, group in group_words.items():
            if word in text:
                requested_group = group
                break

    if wants_distribution:
        group = "sector"
        if re.search(r"sexo", text):
            group = "sex"
        elif re.search(r"nivel", text):
            group = "level"
        elif re.search(r"area", text):
            group = "area"
        elif re.search(r"departamento", text):
            group = "department"
        if departments:
            filters["department"] = departments[0]
        return AgentQuery(metric="distribution", filters=filters, group_by=group)

    if requested_group and not wants_compare:
        if departments:
            filters["department"] = departments[0]
        if wants_withdrawal:
            metric = "withdrawal_rate"
        elif wants_non_promo:
            metric = "non_promotion_rate"
        elif wants_promo:
            metric = "promotion_rate"
        elif wants_repeat:
            metric = "repetition_rate"
        else:
            metric = "enrollment_count"
        return AgentQuery(metric=metric, filters=filters, group_by=requested_group, limit=30)

    if wants_compare and wants_withdrawal and len(areas) >= 2:
        return AgentQuery(
            metric="comparison",
            filters={"area": areas[0]},
            compare_filters={"area": areas[1]},
            rank_metric="withdrawal_rate",
        )

    if wants_compare and len(departments) >= 2:
        metric: Any = "promotion_rate" if wants_promo else "enrollment_count"
        if wants_withdrawal:
            metric = "withdrawal_rate"
        if wants_non_promo:
            metric = "non_promotion_rate"
        return AgentQuery(
            metric="comparison",
            filters={"department": departments[0]},
            compare_filters={"department": departments[1]},
            rank_metric=metric,
        )

    if wants_rank and re.search(r"municip", text) and wants_withdrawal:
        if departments:
            filters["department"] = departments[0]
        return AgentQuery(
            metric="ranking",
            filters=filters,
            group_by="municipality",
            rank_metric="withdrawal_rate",
            limit=10,
        )

    if wants_rank and re.search(r"departamento", text):
        return AgentQuery(metric="ranking", group_by="department", rank_metric="enrollment_count")

    if wants_non_promo:
        if departments:
            filters["department"] = departments[0]
        return AgentQuery(metric="non_promotion_rate", filters=filters)

    if wants_withdrawal:
        if departments:
            filters["department"] = departments[0]
        if len(areas) == 1:
            filters["area"] = areas[0]
        return AgentQuery(metric="withdrawal_rate", filters=filters)

    if wants_promo:
        if departments:
            filters["department"] = departments[0]
        return AgentQuery(metric="promotion_rate", filters=filters)

    if wants_repeat:
        if departments:
            filters["department"] = departments[0]
        return AgentQuery(metric="repetition_rate", filters=filters)

    if departments:
        filters["department"] = departments[0]
    if wants_count or filters:
        return AgentQuery(metric="enrollment_count", filters=filters)

    return AgentQuery(metric="enrollment_count", filters=filters)


def _llm_config() -> tuple[str, str, str] | None:
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    if groq_key:
        return (
            groq_key,
            os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
            os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
        )
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    if openai_key:
        return openai_key, os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"), os.getenv(
            "OPENAI_MODEL", "gpt-4o-mini"
        )
    return None


def language_provider() -> str:
    config = _llm_config()
    if config is None:
        return "Intérprete local"
    return "Groq" if "groq.com" in config[1] else "OpenAI"


def interpret_llm(question: str, previous_query: AgentQuery | None = None) -> AgentQuery:
    from openai import OpenAI

    config = _llm_config()
    if config is None:
        raise RuntimeError("No hay proveedor de lenguaje configurado.")
    api_key, base_url, model = config
    client = OpenAI(api_key=api_key, base_url=base_url)
    context = ""
    if previous_query is not None:
        context = f"\nConsulta anterior para resolver seguimientos: {previous_query.model_dump_json()}"
    completion = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + context},
            {"role": "user", "content": question},
        ],
    )
    content = completion.choices[0].message.content or "{}"
    payload = json.loads(content)
    if payload.get("group_by") not in {None, *FILTER_KEYS}:
        payload["group_by"] = None
    return AgentQuery.model_validate(payload)


def interpret(question: str, previous_query: AgentQuery | None = None) -> AgentQuery:
    if _llm_config() is not None:
        try:
            return interpret_llm(question, previous_query)
        except Exception:
            return interpret_demo(question, previous_query)
    return interpret_demo(question, previous_query)
