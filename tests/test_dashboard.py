"""Pruebas unitarias para los generadores de gráficos y componentes del dashboard."""

from __future__ import annotations

import plotly.graph_objects as go
import polars as pl
import pytest

from src.analytics.indicators import KPISummary
from src.dashboard.charts import (
    create_bar_levels,
    create_donut_results,
    create_gap_bars,
    create_horizontal_ranking,
    create_municipal_bars,
    create_pueblo_breakdown,
)


@pytest.fixture
def sample_kpis() -> KPISummary:
    return KPISummary(
        matricula_total=1000,
        promovidos=850,
        no_promovidos=90,
        retirados=60,
        vigentes=0,
        ignorados=0,
        repitentes=80,
        graduandos=120,
        denominador_terminal=1000,
        tasa_promocion=85.0,
        tasa_no_promocion=9.0,
        tasa_retiro=6.0,
        tasa_repitencia=8.0,
        filters={},
    )


@pytest.fixture
def sample_levels_df() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "nivel": ["Primaria", "Básico", "Diversificado"],
            "matricula": [5000, 3000, 2000],
            "tasa_promocion": [88.5, 82.1, 89.0],
        }
    )


@pytest.fixture
def sample_rank_df() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "departamento": ["Guatemala", "Alta Verapaz", "Quetzaltenango"],
            "matricula": [30000, 15000, 12000],
            "tasa_promocion": [87.5, 79.2, 86.1],
        }
    )


def test_create_donut_results(sample_kpis: KPISummary) -> None:
    fig = create_donut_results(sample_kpis)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    pie = fig.data[0]
    assert pie.values[0] == 850
    assert pie.values[1] == 90
    assert pie.values[2] == 60


def test_create_bar_levels(sample_levels_df: pl.DataFrame) -> None:
    fig = create_bar_levels(sample_levels_df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    bar = fig.data[0]
    assert list(bar.x) == ["Primaria", "Básico", "Diversificado"]


def test_create_horizontal_ranking(sample_rank_df: pl.DataFrame) -> None:
    fig = create_horizontal_ranking(
        df_rank=sample_rank_df,
        metric="matricula",
        title="Test Ranking",
        x_label="Matrícula",
        national_avg=19000.0,
    )
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    bar = fig.data[0]
    assert bar.orientation == "h"


def test_create_municipal_bars() -> None:
    df_mupios = pl.DataFrame(
        {
            "municipio": ["Mixco", "Villa Nueva", "San Juan Sacatepéquez"],
            "matricula": [5000, 4500, 3000],
        }
    )
    fig = create_municipal_bars(df_mupios, metric="matricula", title="Top Municipios")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1


def test_create_gap_bars() -> None:
    df_gap = pl.DataFrame(
        {
            "area": ["Rural", "Urbana"],
            "tasa_promocion": [82.0, 88.0],
            "tasa_no_promocion": [11.0, 7.0],
            "tasa_retiro": [7.0, 5.0],
        }
    )
    fig = create_gap_bars(df_gap, dimension="area", title="Brecha Área")
    assert isinstance(fig, go.Figure)
    # Debe contener 3 barras agrupadas (Promoción, No promoción, Retiro)
    assert len(fig.data) == 3


def test_create_pueblo_breakdown() -> None:
    df_pueblo = pl.DataFrame(
        {
            "pueblo_pertenencia": ["Ladino", "Maya"],
            "matricula": [60000, 40000],
            "tasa_promocion": [86.0, 84.0],
        }
    )
    fig = create_pueblo_breakdown(df_pueblo)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
