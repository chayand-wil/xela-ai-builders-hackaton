"""Pruebas de consultas parametrizadas y allowlist de identificadores."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.analytics.queries import build_where, quote_ident
from src.analytics.service import AnalyticsService
from tests.test_indicators import write_tiny_parquet


@pytest.fixture
def tiny_service(tmp_path: Path) -> AnalyticsService:
    parquet = write_tiny_parquet(tmp_path / "tiny.parquet")
    return AnalyticsService(str(parquet.resolve().as_posix()))


def test_where_uses_placeholders_not_user_sql() -> None:
    sql, params = build_where({"department": "Quetzaltenango'; DROP TABLE x;--"})
    assert "DROP TABLE" not in sql
    assert "?" in sql
    assert params == ["Quetzaltenango'; DROP TABLE x;--"]


def test_quote_ident_rejects_unknown_column() -> None:
    with pytest.raises(ValueError):
        quote_ident("resultado; delete from inscripciones")


def test_grouped_counts_and_limit(tiny_service: AnalyticsService) -> None:
    ranking = tiny_service.compute("ranking", group_by="department", limit=2)
    assert ranking["rows"][0]["label"] == "Quetzaltenango"
    assert ranking["rows"][0]["value"] == 10
    assert len(ranking["rows"]) == 2


def test_comparison_and_invalid_metric(tiny_service: AnalyticsService) -> None:
    compared = tiny_service.compute(
        "comparison",
        filters={"department": "Guatemala"},
        compare_filters={"department": "Quetzaltenango"},
        rank_metric="enrollment_count",
    )
    assert compared["rows"][0]["value"] == 1
    assert compared["rows"][1]["value"] == 10
    assert compared["value"] == 9
    with pytest.raises(ValueError):
        tiny_service.compute("escuelas")


def test_filter_options_sorted(tiny_service: AnalyticsService) -> None:
    options = tiny_service.filter_options()
    assert options["department"] == ["Guatemala", "Quetzaltenango"]
    assert options["outcome"] == sorted(options["outcome"])
