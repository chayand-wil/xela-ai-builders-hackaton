"""Módulo analítico centralizado de Educación Formal 2024 (EduGuate IA)."""

from src.analytics.indicators import KPISummary, MetricResult, calculate_rates
from src.analytics.narratives import explain_breakdown, explain_kpis, explain_ranking
from src.analytics.queries import AnalyticsEngine

__all__ = [
    "AnalyticsEngine",
    "KPISummary",
    "MetricResult",
    "calculate_rates",
    "explain_breakdown",
    "explain_kpis",
    "explain_ranking",
]
