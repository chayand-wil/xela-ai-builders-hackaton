"""Capa analítica: DuckDB calcula; las cifras no salen de Wren ni del LLM."""

from src.analytics.paths import get_parquet_path
from src.analytics.queries import FILTER_KEYS
from src.analytics.service import AnalyticsService, get_analytics

__all__ = ["FILTER_KEYS", "AnalyticsService", "get_analytics", "get_parquet_path"]
