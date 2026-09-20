"""Pruebas unitarias automatizadas para el Agente Conversacional EduGuate IA.

Verifica la arquitectura anti-alucinación, esquemas Pydantic, herramientas analíticas
y la correcta delegación a DuckDB.
"""

from __future__ import annotations

import pytest

from src.agent.engine import EduGuateAgent
from src.agent.schemas import AgentIntent, AgentResponse, QueryCategory
from src.agent.tools import clean_filters, execute_intent
from src.analytics.queries import AnalyticsEngine


@pytest.fixture
def agent() -> EduGuateAgent:
    return EduGuateAgent()


@pytest.fixture
def engine() -> AnalyticsEngine:
    return AnalyticsEngine()


def test_agent_schemas_validation() -> None:
    intent = AgentIntent(
        categoria=QueryCategory.DATA_QUERY,
        filtros={"departamento": "Quetzaltenango", "nivel": "Primaria"},
        metrica="matricula",
        pregunta_normalizada="¿Cuántos estudiantes hay en Quetzaltenango?",
    )
    assert intent.categoria == QueryCategory.DATA_QUERY
    assert intent.filtros["departamento"] == "Quetzaltenango"

    resp = AgentResponse(
        texto="Respuesta de prueba",
        categoria=QueryCategory.DATA_QUERY,
        cifras_calculadas={"matricula": 1000},
        fuente_datos=["DuckDB"],
        latencia_ms=120.5,
        modo_ia="Test",
    )
    assert resp.latencia_ms == 120.5
    assert resp.cifras_calculadas["matricula"] == 1000


def test_fallback_intent_out_of_scope(agent: EduGuateAgent) -> None:
    intent_salary = agent._fallback_intent_parser("¿Cuánto dinero gana un maestro de primaria?")
    assert intent_salary.categoria == QueryCategory.OUT_OF_SCOPE

    intent_computers = agent._fallback_intent_parser("¿Cuántas computadoras hay en las escuelas de Xela?")
    assert intent_computers.categoria == QueryCategory.OUT_OF_SCOPE

    intent_year = agent._fallback_intent_parser("¿Cómo fue la matrícula en 2015?")
    assert intent_year.categoria == QueryCategory.OUT_OF_SCOPE


def test_fallback_intent_data_query(agent: EduGuateAgent) -> None:
    intent = agent._fallback_intent_parser("¿Cuál es la tasa de deserción en Quetzaltenango en sector público?")
    assert intent.categoria == QueryCategory.DATA_QUERY
    assert intent.filtros.get("departamento") == "Quetzaltenango"
    assert intent.filtros.get("sector") == "Oficial"
    assert intent.metrica == "tasa_retiro"


def test_execute_intent_data_query(engine: AnalyticsEngine) -> None:
    intent = AgentIntent(
        categoria=QueryCategory.DATA_QUERY,
        filtros={"departamento": "Guatemala"},
        metrica="matricula",
        pregunta_normalizada="Matrícula en Guatemala",
    )
    res = execute_intent(intent, engine)
    assert res["tipo"] == "kpis_generales"
    assert res["indicadores"]["matricula_total"] > 0
    assert "narrativa" in res


def test_execute_intent_out_of_scope(engine: AnalyticsEngine) -> None:
    intent = AgentIntent(
        categoria=QueryCategory.OUT_OF_SCOPE,
        razon_fuera_de_alcance="Dato no disponible en censo 2024",
    )
    res = execute_intent(intent, engine)
    assert res["tipo"] == "fuera_de_alcance"
    assert len(res["variables_disponibles"]) > 0


def test_clean_filters() -> None:
    raw = {"departamento": "Guatemala", "municipio": None, "nivel": "", "sector": "Todos"}
    cleaned = clean_filters(raw)
    assert cleaned == {"departamento": "Guatemala"}


def test_agent_ask_total_matricula(agent: EduGuateAgent) -> None:
    resp = agent.ask("¿Cuántos estudiantes se matricularon en total en 2024?")
    assert isinstance(resp, AgentResponse)
    assert resp.categoria == QueryCategory.DATA_QUERY
    assert resp.latencia_ms > 0
    assert "4,298,887" in resp.texto or "4298887" in str(resp.cifras_calculadas)


def test_agent_out_of_scope_guardrail(agent: EduGuateAgent) -> None:
    resp = agent.ask("¿Cuál es el presupuesto financiero del Ministerio de Educación en 2024?")
    assert resp.categoria == QueryCategory.OUT_OF_SCOPE
    assert "no" in resp.texto.lower()
