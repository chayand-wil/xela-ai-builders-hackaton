"""Esquema Pydantic de intención del agente. El modelo no calcula cifras."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from src.analytics.queries import FILTER_KEYS

MetricLiteral = Literal[
    "enrollment_count",
    "promotion_rate",
    "non_promotion_rate",
    "withdrawal_rate",
    "repetition_rate",
    "distribution",
    "ranking",
    "comparison",
]


class AgentQuery(BaseModel):
    metric: MetricLiteral
    filters: dict[str, Any] = Field(default_factory=dict)
    group_by: str | None = None
    limit: int = 10
    compare_filters: dict[str, Any] | None = None
    rank_metric: MetricLiteral | None = None

    @field_validator("limit")
    @classmethod
    def _limit_range(cls, value: int) -> int:
        if value < 1:
            return 1
        if value > 50:
            return 50
        return value

    @field_validator("filters")
    @classmethod
    def _known_filter_keys(cls, value: dict[str, Any]) -> dict[str, Any]:
        unknown = [key for key in value if key not in FILTER_KEYS]
        if unknown:
            raise ValueError(f"Filtros no permitidos: {unknown}")
        return value

    @field_validator("compare_filters")
    @classmethod
    def _known_compare_keys(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if not value:
            return value
        unknown = [key for key in value if key not in FILTER_KEYS]
        if unknown:
            raise ValueError(f"Filtros de comparación no permitidos: {unknown}")
        return value

    @field_validator("group_by")
    @classmethod
    def _known_group(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value not in FILTER_KEYS:
            raise ValueError(f"group_by no permitido: {value}")
        return value
