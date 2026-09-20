"""Agente conversacional: interpreta, valida y llama a la capa analítica."""

from __future__ import annotations

from typing import Any

from src.agent.guardrails import inspect_question
from src.agent.interpreter import interpret
from src.agent.responses import format_answer
from src.agent.schemas import AgentQuery
from src.analytics.service import get_analytics


def ask(question: str, extra_filters: dict | None = None) -> dict[str, Any]:
    """Responde una pregunta. status: ok | reject | clarify."""
    status, message = inspect_question(question)
    if status != "ok":
        return {"answer": message, "query": None, "result": None, "status": status}

    try:
        query = interpret(question)
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

    return {
        "answer": format_answer(query, result),
        "query": query.model_dump(),
        "result": result,
        "status": "ok",
    }


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
