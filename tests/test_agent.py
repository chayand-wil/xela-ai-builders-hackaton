"""Pruebas del agente: válidas, imposible y ambigua. Modo demo sin API."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.agent import ask
from src.analytics.service import AnalyticsService, get_analytics
from tests.test_indicators import write_tiny_parquet


@pytest.fixture
def demo_agent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AnalyticsService:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    parquet = write_tiny_parquet(tmp_path / "tiny.parquet")
    service = AnalyticsService(str(parquet.resolve().as_posix()))
    get_analytics.cache_clear()
    monkeypatch.setattr("src.agent.get_analytics", lambda: service)
    yield service
    get_analytics.cache_clear()


def test_valid_enrollment_question(demo_agent: AnalyticsService) -> None:
    payload = ask("¿Cuántas inscripciones hay en Quetzaltenango?")
    assert payload["status"] == "ok"
    assert payload["query"]["metric"] == "enrollment_count"
    assert payload["result"]["value"] == 10
    assert "10" in payload["answer"]


def test_valid_distribution_question(demo_agent: AnalyticsService) -> None:
    payload = ask("¿Cómo se distribuyen las inscripciones por sector?")
    assert payload["status"] == "ok"
    assert payload["query"]["metric"] == "distribution"
    assert payload["query"]["group_by"] == "sector"
    labels = {row["label"] for row in payload["result"]["rows"]}
    assert "Público" in labels


def test_impossible_grades_question(demo_agent: AnalyticsService) -> None:
    payload = ask("¿Cuál fue la nota promedio de los estudiantes?")
    assert payload["status"] == "reject"
    assert payload["result"] is None
    assert "notas" in payload["answer"].lower() or "fuera del alcance" in payload["answer"].lower()


def test_ambiguous_best_department(demo_agent: AnalyticsService) -> None:
    payload = ask("¿Cuál es el mejor departamento?")
    assert payload["status"] == "clarify"
    assert payload["result"] is None
