"""Esquemas de datos tipados (Pydantic) para el Agente Conversacional EduGuate IA.

Garantizan la validación estricta de intenciones de consulta, parámetros analíticos
y respuestas enriquecidas con metadatos de verificación y latencia.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class QueryCategory(str, Enum):
    """Categoría semántica de la consulta del usuario."""

    DATA_QUERY = "DATA_QUERY"  # Consulta de cifras, matrícula, tasas o rankings
    ANALYSIS_QUERY = "ANALYSIS_QUERY"  # Pregunta sobre conclusiones o interpretaciones del dashboard
    OUT_OF_SCOPE = "OUT_OF_SCOPE"  # Consulta de datos no incluidos en el Censo 2024
    GREETING = "GREETING"  # Saludo o solicitud de ayuda/orientación


class AgentIntent(BaseModel):
    """Esquema de intención estructurada extraída de la pregunta del usuario."""

    categoria: QueryCategory = Field(description="Categoría clasificada de la consulta del usuario.")
    filtros: dict[str, Any] = Field(
        default_factory=dict,
        description="Filtros normalizados con nombres exactos de columnas (e.g. departamento, nivel, sector).",
    )
    dimension: str | None = Field(
        default=None,
        description="Dimensión categórica solicitada para desglose o agrupación (e.g. nivel, sector, area, sexo).",
    )
    metrica: str | None = Field(
        default=None,
        description="Métrica solicitada (matricula, tasa_promocion, tasa_no_promocion, tasa_retiro, repitentes).",
    )
    es_ranking: bool = Field(
        default=False,
        description="Indica si la pregunta solicita un ranking (ej. departamento con mayor/menor valor).",
    )
    pregunta_normalizada: str = Field(
        default="",
        description="Pregunta del usuario reescrita de manera clara en español.",
    )
    razon_fuera_de_alcance: str | None = Field(
        default=None,
        description="Explicación si la consulta no puede ser respondida con el dataset de 2024.",
    )


class AgentResponse(BaseModel):
    """Respuesta final enriquecida del Agente Conversacional."""

    texto: str = Field(description="Explicación ejecutiva en lenguaje natural dirigida a usuarios no técnicos.")
    categoria: QueryCategory = Field(description="Categoría resuelta de la consulta.")
    cifras_calculadas: dict[str, Any] = Field(
        default_factory=dict,
        description="Valores matemáticos exactos calculados por DuckDB (fuente de verdad).",
    )
    fuente_datos: list[str] = Field(
        default_factory=list,
        description="Tablas, vistas o indicadores consultados para resolver la pregunta.",
    )
    latencia_ms: float = Field(
        default=0.0,
        description="Tiempo total de inferencia y cálculo en milisegundos.",
    )
    modo_ia: str = Field(
        default="Groq LPU",
        description="Indica si se utilizó Groq LLM o el motor determinista local de respaldo.",
    )
