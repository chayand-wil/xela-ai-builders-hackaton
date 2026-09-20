"""Pruebas unitarias para el motor analítico y consultas DuckDB (Fase 2)."""

import pytest

from src.analytics.indicators import calculate_rates
from src.analytics.narratives import explain_breakdown, explain_kpis, explain_ranking
from src.analytics.queries import AnalyticsEngine


@pytest.fixture(scope="session")
def engine() -> AnalyticsEngine:
    return AnalyticsEngine()


def test_calculate_rates_pure() -> None:
    """Verifica que la función pura calculate_rates aplique las fórmulas oficiales."""
    rates = calculate_rates(
        promovidos=800,
        no_promovidos=150,
        retirados=50,
        matricula_total=1050,
        repitentes=100,
    )
    # Denominador = 800 + 150 + 50 = 1000
    assert rates["denominador_terminal"] == 1000
    assert rates["tasa_promocion"] == 80.0
    assert rates["tasa_no_promocion"] == 15.0
    assert rates["tasa_retiro"] == 5.0
    # Repitencia sobre matricula_total = 100 / 1050 * 100 ≈ 9.52%
    assert rates["tasa_repitencia"] == 9.52


def test_kpis_national_total(engine: AnalyticsEngine) -> None:
    """Verifica los KPIs a nivel nacional sobre el dataset completo."""
    kpis = engine.get_kpis()
    assert kpis.matricula_total == 4298887
    assert kpis.promovidos == 3664211
    assert kpis.no_promovidos == 394880
    assert kpis.retirados == 237615
    assert kpis.denominador_terminal == 3664211 + 394880 + 237615
    # Suma de tasas terminales debe aproximarse al 100%
    suma_tasas = kpis.tasa_promocion + kpis.tasa_no_promocion + kpis.tasa_retiro
    assert abs(suma_tasas - 100.0) < 0.1


def test_kpis_with_filters(engine: AnalyticsEngine) -> None:
    """Verifica que los filtros aplicados a los KPIs restrinjan el conteo con precisión."""
    kpis_xela = engine.get_kpis({"departamento": "Quetzaltenango"})
    assert kpis_xela.matricula_total == 232627
    assert kpis_xela.filters == {"departamento": "Quetzaltenango"}

    kpis_gt = engine.get_kpis({"departamento": "Guatemala"})
    assert kpis_gt.matricula_total == 863879


def test_breakdown_by_dimension(engine: AnalyticsEngine) -> None:
    """Verifica el desglose por nivel educativo y consistencia de totales."""
    df_nivel = engine.get_breakdown_by_dimension("nivel")
    assert len(df_nivel) == 5  # Primaria, Básico, Preprimaria, Diversificado, Primaria de adultos
    # Suma de matrícula debe ser igual al total nacional
    assert df_nivel["matricula"].sum() == 4298887
    assert "tasa_promocion" in df_nivel.columns
    assert "tasa_retiro" in df_nivel.columns


def test_department_ranking(engine: AnalyticsEngine) -> None:
    """Verifica el ranking de los 22 departamentos."""
    df_rank = engine.get_department_ranking(metric="matricula", ascending=False)
    assert len(df_rank) == 22
    # El primer lugar en matrícula debe ser el departamento de Guatemala
    assert df_rank["departamento"][0] == "Guatemala"
    assert df_rank["matricula"][0] == 863879


def test_municipal_breakdown(engine: AnalyticsEngine) -> None:
    """Verifica el desglose municipal de un departamento."""
    df_mupios_gt = engine.get_municipal_breakdown("Guatemala")
    # Exactamente 17 municipios en el departamento de Guatemala
    assert len(df_mupios_gt) == 17
    assert df_mupios_gt["matricula"].sum() == 863879


def test_cross_tabulation(engine: AnalyticsEngine) -> None:
    """Verifica la tabulación cruzada entre sector y área."""
    df_cross = engine.get_cross_tabulation("sector", "area")
    assert not df_cross.is_empty()
    assert df_cross["total"].sum() == 4298887


def test_narratives(engine: AnalyticsEngine) -> None:
    """Verifica que las funciones narrativas generen textos coherentes y formateados."""
    kpis = engine.get_kpis({"departamento": "Quetzaltenango"})
    narrativa_kpi = explain_kpis(kpis)
    assert "Quetzaltenango" in narrativa_kpi
    assert "232,627" in narrativa_kpi
    assert "%" in narrativa_kpi

    df_rank = engine.get_department_ranking(metric="tasa_retiro")
    narrativa_rank = explain_ranking(
        df_rank, dimension="departamento", metric="tasa_retiro", metric_label="Tasa de Retiro"
    )
    assert "puntos porcentuales" in narrativa_rank
    assert "desigualdades" in narrativa_rank

    df_nivel = engine.get_breakdown_by_dimension("nivel")
    narrativa_nivel = explain_breakdown(df_nivel, "nivel")
    assert "Primaria" in narrativa_nivel
