"""Módulo de fórmulas matemáticas, indicadores y contratos de datos analíticos.

Garantiza que el Dashboard y el Agente de IA compartan exactamente las mismas
definiciones matemáticas oficiales (ADR-004).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MetricResult(BaseModel):
    """Contrato tipado para el retorno de cualquier métrica individual calculada."""

    metric: str
    value: float
    unit: str = "porcentaje"
    label: str
    numerator: int | None = None
    denominator: int | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    description: str | None = None


class KPISummary(BaseModel):
    """Resumen consolidado de indicadores clave (KPIs) para un conjunto de filtros."""

    matricula_total: int
    promovidos: int
    no_promovidos: int
    retirados: int  # Agrupa Retirado y Retirado definitivo
    vigentes: int
    ignorados: int
    repitentes: int
    graduandos: int
    denominador_terminal: int
    tasa_promocion: float
    tasa_no_promocion: float
    tasa_retiro: float
    tasa_repitencia: float
    filters: dict[str, Any] = Field(default_factory=dict)


def calculate_rates(
    promovidos: int,
    no_promovidos: int,
    retirados: int,
    matricula_total: int,
    repitentes: int = 0,
) -> dict[str, float]:
    """Calcula las tasas oficiales de cierre de ciclo y repitencia.

    Fórmulas oficiales (ADR-004):
    - Denominador terminal = Promovidos + No promovidos + Retirados
    - Tasa de Promoción = Promovidos / Denominador terminal * 100
    - Tasa de No Promoción = No promovidos / Denominador terminal * 100
    - Tasa de Retiro = Retirados / Denominador terminal * 100
    - Tasa de Repitencia = Repitentes / Matricula total * 100
    """
    denominador = promovidos + no_promovidos + retirados

    if denominador > 0:
        tasa_prom = round((promovidos / denominador) * 100.0, 2)
        tasa_no_prom = round((no_promovidos / denominador) * 100.0, 2)
        tasa_ret = round((retirados / denominador) * 100.0, 2)
    else:
        tasa_prom = 0.0
        tasa_no_prom = 0.0
        tasa_ret = 0.0

    tasa_rep = round((repitentes / matricula_total) * 100.0, 2) if matricula_total > 0 else 0.0

    return {
        "denominador_terminal": denominador,
        "tasa_promocion": tasa_prom,
        "tasa_no_promocion": tasa_no_prom,
        "tasa_retiro": tasa_ret,
        "tasa_repitencia": tasa_rep,
    }
