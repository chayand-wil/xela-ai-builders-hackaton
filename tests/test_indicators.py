"""Pruebas de fórmulas de tasas con un Parquet mínimo verificable a mano."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from src.analytics.indicators import non_promotion_parts, promotion_parts, rate_denominator, withdrawal_parts
from src.analytics.narratives import describe_ranking
from src.analytics.service import AnalyticsService, get_analytics

TINY_ROWS = [
    {
        "anio": 2024,
        "codigo_establecimiento": "09-01-0001-43",
        "departamento_codigo": 9,
        "departamento": "Quetzaltenango",
        "municipio_codigo": "0901",
        "municipio": "Quetzaltenango",
        "sector": "Público",
        "area": "Urbana",
        "sexo": "Hombre",
        "grado": 1,
        "nivel": "Primaria",
        "pueblo_pertenencia": "Maya",
        "plan_estudios": "Diario",
        "jornada": "Matutina",
        "resultado": "Promovido",
        "repitente": "Sí",
        "graduando": "No es graduando",
    },
    {
        "anio": 2024,
        "codigo_establecimiento": "09-01-0001-43",
        "departamento_codigo": 9,
        "departamento": "Quetzaltenango",
        "municipio_codigo": "0901",
        "municipio": "Quetzaltenango",
        "sector": "Público",
        "area": "Urbana",
        "sexo": "Mujer",
        "grado": 1,
        "nivel": "Primaria",
        "pueblo_pertenencia": "Maya",
        "plan_estudios": "Diario",
        "jornada": "Matutina",
        "resultado": "Promovido",
        "repitente": "Sí",
        "graduando": "No es graduando",
    },
    {
        "anio": 2024,
        "codigo_establecimiento": "09-01-0001-43",
        "departamento_codigo": 9,
        "departamento": "Quetzaltenango",
        "municipio_codigo": "0901",
        "municipio": "Quetzaltenango",
        "sector": "Público",
        "area": "Urbana",
        "sexo": "Hombre",
        "grado": 1,
        "nivel": "Primaria",
        "pueblo_pertenencia": "Maya",
        "plan_estudios": "Diario",
        "jornada": "Matutina",
        "resultado": "Promovido",
        "repitente": "Sí",
        "graduando": "No es graduando",
    },
    {
        "anio": 2024,
        "codigo_establecimiento": "09-01-0001-43",
        "departamento_codigo": 9,
        "departamento": "Quetzaltenango",
        "municipio_codigo": "0901",
        "municipio": "Quetzaltenango",
        "sector": "Privado",
        "area": "Urbana",
        "sexo": "Mujer",
        "grado": 3,
        "nivel": "Básico",
        "pueblo_pertenencia": "Ladino/Mestizo",
        "plan_estudios": "Diario",
        "jornada": "Vespertina",
        "resultado": "Promovido",
        "repitente": "No",
        "graduando": "No es graduando",
    },
    {
        "anio": 2024,
        "codigo_establecimiento": "01-01-0001-43",
        "departamento_codigo": 1,
        "departamento": "Guatemala",
        "municipio_codigo": "0101",
        "municipio": "Guatemala",
        "sector": "Público",
        "area": "Urbana",
        "sexo": "Hombre",
        "grado": 1,
        "nivel": "Primaria",
        "pueblo_pertenencia": "Ladino/Mestizo",
        "plan_estudios": "Diario",
        "jornada": "Matutina",
        "resultado": "Promovido",
        "repitente": "No",
        "graduando": "No es graduando",
    },
    {
        "anio": 2024,
        "codigo_establecimiento": "09-01-0002-43",
        "departamento_codigo": 9,
        "departamento": "Quetzaltenango",
        "municipio_codigo": "0901",
        "municipio": "Quetzaltenango",
        "sector": "Público",
        "area": "Urbana",
        "sexo": "Hombre",
        "grado": 2,
        "nivel": "Primaria",
        "pueblo_pertenencia": "Maya",
        "plan_estudios": "Diario",
        "jornada": "Matutina",
        "resultado": "No promovido",
        "repitente": "No",
        "graduando": "No es graduando",
    },
    {
        "anio": 2024,
        "codigo_establecimiento": "09-01-0002-43",
        "departamento_codigo": 9,
        "departamento": "Quetzaltenango",
        "municipio_codigo": "0901",
        "municipio": "Quetzaltenango",
        "sector": "Público",
        "area": "Urbana",
        "sexo": "Mujer",
        "grado": 2,
        "nivel": "Básico",
        "pueblo_pertenencia": "Maya",
        "plan_estudios": "Diario",
        "jornada": "Matutina",
        "resultado": "No promovido",
        "repitente": "No",
        "graduando": "No es graduando",
    },
    {
        "anio": 2024,
        "codigo_establecimiento": "09-02-0001-43",
        "departamento_codigo": 9,
        "departamento": "Quetzaltenango",
        "municipio_codigo": "0902",
        "municipio": "Salcajá",
        "sector": "Público",
        "area": "Rural",
        "sexo": "Hombre",
        "grado": 1,
        "nivel": "Primaria",
        "pueblo_pertenencia": "Maya",
        "plan_estudios": "Diario",
        "jornada": "Matutina",
        "resultado": "Retirado",
        "repitente": "No",
        "graduando": "No es graduando",
    },
    {
        "anio": 2024,
        "codigo_establecimiento": "09-02-0001-43",
        "departamento_codigo": 9,
        "departamento": "Quetzaltenango",
        "municipio_codigo": "0902",
        "municipio": "Salcajá",
        "sector": "Público",
        "area": "Rural",
        "sexo": "Mujer",
        "grado": 1,
        "nivel": "Primaria",
        "pueblo_pertenencia": "Maya",
        "plan_estudios": "Diario",
        "jornada": "Matutina",
        "resultado": "Retirado definitivo",
        "repitente": "No",
        "graduando": "No es graduando",
    },
    {
        "anio": 2024,
        "codigo_establecimiento": "09-01-0003-43",
        "departamento_codigo": 9,
        "departamento": "Quetzaltenango",
        "municipio_codigo": "0901",
        "municipio": "Quetzaltenango",
        "sector": "Municipal",
        "area": "Urbana",
        "sexo": "Hombre",
        "grado": 1,
        "nivel": "Primaria",
        "pueblo_pertenencia": "Maya",
        "plan_estudios": "Diario",
        "jornada": "Matutina",
        "resultado": "Vigente",
        "repitente": "No",
        "graduando": "No es graduando",
    },
    {
        "anio": 2024,
        "codigo_establecimiento": "09-01-0003-43",
        "departamento_codigo": 9,
        "departamento": "Quetzaltenango",
        "municipio_codigo": "0901",
        "municipio": "Quetzaltenango",
        "sector": "Cooperativa",
        "area": "Urbana",
        "sexo": "Mujer",
        "grado": 1,
        "nivel": "Primaria",
        "pueblo_pertenencia": "Maya",
        "plan_estudios": "Diario",
        "jornada": "Matutina",
        "resultado": "Ignorado",
        "repitente": "Ignorado",
        "graduando": "Ignorado",
    },
]


def write_tiny_parquet(path: Path) -> Path:
    pl.DataFrame(TINY_ROWS).write_parquet(path)
    return path


@pytest.fixture
def tiny_service(tmp_path: Path) -> AnalyticsService:
    parquet = write_tiny_parquet(tmp_path / "tiny.parquet")
    return AnalyticsService(str(parquet.resolve().as_posix()))


def test_manual_rate_denominator_and_rates(tiny_service: AnalyticsService) -> None:
    counts = tiny_service.store.outcome_counts()
    assert rate_denominator(counts) == 9
    promo, num, den = promotion_parts(counts)
    assert num == 5 and den == 9
    assert promo == pytest.approx(5 / 9 * 100)
    non, non_n, _ = non_promotion_parts(counts)
    assert non_n == 2
    assert non == pytest.approx(2 / 9 * 100)
    wit, wit_n, _ = withdrawal_parts(counts)
    assert wit_n == 2
    assert wit == pytest.approx(2 / 9 * 100)
    kpis = tiny_service.kpis()
    assert kpis["enrollment_count"]["value"] == 11
    assert kpis["vigente_count"] == 1
    assert kpis["ignorado_count"] == 1
    assert kpis["promotion_rate"]["value"] == pytest.approx(5 / 9 * 100)


def test_repetition_excludes_ignorado(tiny_service: AnalyticsService) -> None:
    result = tiny_service.compute("repetition_rate")
    assert result["numerator"] == 3
    assert result["denominator"] == 10
    assert result["value"] == pytest.approx(30.0)


def test_qx_filter_and_distribution(tiny_service: AnalyticsService) -> None:
    qx = tiny_service.compute("enrollment_count", filters={"department": "Quetzaltenango"})
    assert qx["value"] == 10
    dist = tiny_service.distribution("sector", filters={"department": "Quetzaltenango"})
    by_label = {row["label"]: row["value"] for row in dist["rows"]}
    assert by_label["Público"] == 7
    assert by_label["Privado"] == 1


def test_kpis_against_real_parquet() -> None:
    get_analytics.cache_clear()
    kpis = get_analytics().kpis()
    enrollment = kpis["enrollment_count"]["value"]
    assert enrollment in {10_000, 4_298_887} or enrollment > 9_000
    assert kpis["promotion_rate"]["denominator"] > 0
    assert "percent" == kpis["promotion_rate"]["unit"]
    get_analytics.cache_clear()


def test_narratives_translate_internal_dimension_and_filters() -> None:
    text = describe_ranking(
        "municipality",
        [{"label": "Cobán", "value": 9397}],
        "count",
        {"shift": "Vespertina", "department": "Alta Verapaz"},
    )
    assert "por municipio" in text
    assert "jornada: Vespertina" in text
    assert "departamento: Alta Verapaz" in text
    assert "municipality" not in text
    assert "shift=" not in text
    assert "department=" not in text
