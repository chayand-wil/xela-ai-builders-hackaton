"""Agente conversacional: interpreta, valida y llama a la capa analítica."""

from __future__ import annotations

from typing import Any

from src.agent.guardrails import fold, inspect_question
from src.agent.interpreter import interpret
from src.agent.responses import format_answer
from src.agent.schemas import AgentQuery
from src.analytics.service import get_analytics


def ask(
    question: str,
    extra_filters: dict | None = None,
    history: list[dict[str, Any]] | None = None,
    audience: str = "Público general",
) -> dict[str, Any]:
    """Responde una pregunta. status: ok | reject | clarify."""
    conceptual = _conceptual_answer(question)
    if conceptual:
        return {
            "answer": conceptual,
            "query": None,
            "result": None,
            "status": "ok",
            "provider": "Contexto educativo gobernado de EduGuate IA",
            "related_questions": [
                "¿Cuál es la tasa de retiro con mis filtros?",
                "¿Qué datos se excluyen del cálculo?",
                "¿Por qué una diferencia no demuestra una causa?",
            ],
        }
    status, message = inspect_question(question)
    if status != "ok":
        return {"answer": message, "query": None, "result": None, "status": status}

    try:
        previous_query = _previous_query(history)
        query = interpret(question, previous_query=previous_query)
    except Exception:
        return {
            "answer": "No pude interpretar la pregunta. Prueba con un departamento, nivel o tasa concreta.",
            "query": None,
            "result": None,
            "status": "clarify",
        }

    merged = dict(query.filters)
    if extra_filters:
        merged.update({key: value for key, value in extra_filters.items() if value not in (None, "", "Todos")})
        query = query.model_copy(update={"filters": merged})

    try:
        result = _run_query(query)
    except ValueError as exc:
        return {"answer": str(exc), "query": query.model_dump(), "result": None, "status": "clarify"}

    expanded = bool(
        previous_query
        and any(word in fold(question) for word in ("detalle", "explica", "facil", "denominador"))
    )
    provider = _verify_with_wren(query, result)
    return {
        "answer": format_answer(query, result, audience=audience, expanded=expanded),
        "query": query.model_dump(),
        "result": result,
        "status": "ok",
        "provider": provider,
        "related_questions": _related_questions(query),
    }


def _conceptual_answer(question: str) -> str | None:
    text = fold(question)
    asks_definition = any(phrase in text for phrase in ("que significa", "que es", "como se calcula", "que mide"))
    if asks_definition and "retiro" in text:
        return (
            "La tasa de retiro indica cuántas inscripciones terminaron como Retirado o Retirado definitivo "
            "por cada 100 inscripciones con resultado final conocido. No incluye Vigente ni Ignorado. "
            "No explica por qué ocurrió el retiro; solo muestra su frecuencia en los datos de 2024."
        )
    if asks_definition and ("promocion" in text or "promov" in text):
        return (
            "La tasa de promoción indica cuántas inscripciones terminaron como Promovido por cada 100 "
            "con resultado final conocido. Vigente e Ignorado quedan fuera del denominador."
        )
    if asks_definition and ("inscripcion" in text or "matricula" in text):
        return (
            "Una inscripción es un registro administrativo del ciclo escolar 2024. No equivale necesariamente "
            "a una persona única, por lo que la aplicación evita decir 'cantidad de estudiantes únicos'."
        )
    if text.startswith(("por que", "¿por que")):
        return (
            "Estos datos permiten observar diferencias, pero no identificar sus causas. Para explicar un porqué "
            "harían falta variables adicionales —por ejemplo contexto económico, infraestructura o docentes— "
            "que no están presentes en este dataset."
        )
    return None


def _previous_query(history: list[dict[str, Any]] | None) -> AgentQuery | None:
    for item in reversed(history or []):
        content = item.get("content") if isinstance(item, dict) else None
        if isinstance(content, dict) and content.get("query"):
            try:
                return AgentQuery.model_validate(content["query"])
            except Exception:  # noqa: BLE001
                continue
    return None


def _related_questions(query: AgentQuery) -> list[str]:
    dimension = query.group_by or "municipality"
    options = [
        "Explícamelo con palabras más sencillas.",
        "Dame más detalles del numerador y denominador.",
    ]
    if dimension != "municipality":
        options.append("¿Y cómo se ve por municipio?")
    else:
        options.append("¿Y cómo se distribuye por sector?")
    return options


def _verify_with_wren(query: AgentQuery, result: dict[str, Any]) -> str:
    """Verifica consultas escalares sencillas en Wren; nunca bloquea el fallback."""
    if query.metric != "enrollment_count" or query.group_by or query.compare_filters:
        return "DuckDB (consulta determinista)"
    try:
        from src.analytics.queries import FILTER_KEYS
        from src.integrations.wren import WrenClient

        clauses = []
        for key, value in query.filters.items():
            column = FILTER_KEYS[key]
            escaped = str(value).replace("'", "''")
            clauses.append(f'"{column}" = \'{escaped}\'')
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        rows = WrenClient().query(f'SELECT COUNT(*) AS total FROM "inscripciones"{where}', limit=1).rows
        if rows and int(rows[0]["total"]) == int(result["value"]):
            return "WrenAI, verificado con DuckDB"
    except Exception:  # noqa: BLE001
        pass
    return "DuckDB (WrenAI no disponible; respaldo automático)"


def _run_query(query: AgentQuery) -> dict[str, Any]:
    service = get_analytics()
    inner = query.rank_metric
    return service.compute(
        metric=query.metric,
        filters=query.filters,
        group_by=query.group_by,
        limit=query.limit,
        compare_filters=query.compare_filters,
        rank_metric=inner,
    )


__all__ = ["AgentQuery", "ask"]
