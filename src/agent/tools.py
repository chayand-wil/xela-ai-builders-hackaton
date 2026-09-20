"""Herramientas analíticas deterministas para la ejecución de intenciones del Agente Conversacional.

Mapea intenciones estructuradas a consultas SQL optimizadas en DuckDB (< 50ms)
y genera el bloque de hechos verificados para el LLM.
"""

from __future__ import annotations

import logging
from typing import Any

from src.agent.schemas import AgentIntent, QueryCategory
from src.analytics.narratives import explain_breakdown, explain_kpis, explain_ranking
from src.analytics.queries import AnalyticsEngine

logger = logging.getLogger(__name__)


def clean_filters(raw_filters: dict[str, Any]) -> dict[str, Any]:
    """Elimina filtros vacíos o nulos."""
    cleaned: dict[str, Any] = {}
    for k, v in raw_filters.items():
        if v is not None and v != "" and v != "null" and v != "Todos":
            cleaned[k] = v
    return cleaned


def execute_intent(intent: AgentIntent, engine: AnalyticsEngine) -> dict[str, Any]:
    """Ejecuta la consulta analítica exacta sobre DuckDB según la intención clasificada."""
    cat = intent.categoria

    # 1. Caso: Saludo o solicitud de orientación
    if cat == QueryCategory.GREETING:
        return {
            "tipo": "saludo",
            "alcance": (
                "Puedo responder preguntas sobre los 4,298,887 estudiantes del Censo Escolar 2024 del INE. "
                "Por ejemplo: matrícula por departamento o municipio, tasas de aprobación y deserción escolar, "
                "diferencias entre colegios públicos y privados, o brechas entre la zona rural y urbana."
            ),
        }

    # 2. Caso: Consulta fuera de alcance (Anti-Alucinación)
    if cat == QueryCategory.OUT_OF_SCOPE:
        return {
            "tipo": "fuera_de_alcance",
            "razon": intent.razon_fuera_de_alcance
            or "La pregunta solicita información no recopilada en el Censo de Educación Formal 2024 del INE.",
            "variables_disponibles": [
                "Matrícula total por departamento y 340 municipios",
                "Niveles educativos (Preprimaria, Primaria, Básico, Diversificado)",
                "Sectores (Oficial, Privado, Municipal, Cooperativa)",
                "Área geográfica (Rural, Urbana)",
                "Resultados académicos terminales (Promovido, No promovido, Retirado)",
                "Población repitente y cohorte de graduandos",
                "Pueblo de pertenencia étnica",
            ],
        }

    # 3. Caso: Pregunta sobre conclusiones e interpretaciones del dashboard
    if cat == QueryCategory.ANALYSIS_QUERY:
        kpis_nat = engine.get_kpis()
        df_niveles = engine.get_breakdown_by_dimension("nivel")
        df_area = engine.get_breakdown_by_dimension("area")
        df_sector = engine.get_breakdown_by_dimension("sector")

        return {
            "tipo": "analisis_dashboard",
            "indicadores_nacionales": {
                "matricula_total": kpis_nat.matricula_total,
                "tasa_promocion_nacional": f"{kpis_nat.tasa_promocion:.1f}%",
                "tasa_no_promocion_nacional": f"{kpis_nat.tasa_no_promocion:.1f}%",
                "tasa_retiro_nacional": f"{kpis_nat.tasa_retiro:.1f}%",
                "repitentes": kpis_nat.repitentes,
            },
            "desglose_area_rural_urbana": df_area.to_dicts(),
            "desglose_niveles": df_niveles.to_dicts(),
            "desglose_sector": df_sector.to_dicts(),
            "narrativas_oficiales": {
                "explicacion_kpis": explain_kpis(kpis_nat),
                "analisis_niveles": explain_breakdown(df_niveles, "nivel"),
                "analisis_area": explain_breakdown(df_area, "area"),
                "analisis_sector": explain_breakdown(df_sector, "sector"),
            },
        }

    # 4. Caso: Consulta cuantitativa de datos (DATA_QUERY)
    filtros = clean_filters(intent.filtros)

    # Subcaso A: Ranking departamental
    if intent.es_ranking or (intent.metrica and "tasa" in intent.metrica and not intent.dimension):
        metrica = intent.metrica or "matricula"
        df_rank = engine.get_department_ranking(metric=metrica, filters=filtros)
        if not df_rank.is_empty():
            top = df_rank.row(0, named=True)
            bottom = df_rank.row(-1, named=True)
            return {
                "tipo": "ranking_departamentos",
                "metrica": metrica,
                "primer_lugar": top,
                "ultimo_lugar": bottom,
                "top_5": df_rank.head(5).to_dicts(),
                "narrativa": explain_ranking(df_rank, dimension="departamento", metric=metrica),
            }

    # Subcaso B: Desglose por una dimensión específica
    if intent.dimension and intent.dimension in [
        "nivel",
        "sector",
        "area",
        "sexo",
        "departamento",
        "pueblo_pertenencia",
    ]:
        df_dim = engine.get_breakdown_by_dimension(intent.dimension, filters=filtros)
        return {
            "tipo": f"desglose_por_{intent.dimension}",
            "dimension": intent.dimension,
            "registros": df_dim.to_dicts(),
            "narrativa": explain_breakdown(df_dim, intent.dimension),
        }

    # Subcaso C: Desglose municipal si se consultó por municipio o departamento
    if "municipio" in filtros:
        kpis_mupio = engine.get_kpis(filtros)
        return {
            "tipo": "kpis_municipales",
            "filtros": filtros,
            "indicadores": kpis_mupio.model_dump(),
            "narrativa": explain_kpis(kpis_mupio),
        }

    # Subcaso D: KPIs generales para los filtros dados
    kpis = engine.get_kpis(filtros)
    return {
        "tipo": "kpis_generales",
        "filtros": filtros,
        "indicadores": {
            "matricula_total": kpis.matricula_total,
            "promovidos": kpis.promovidos,
            "tasa_promocion": kpis.tasa_promocion,
            "no_promovidos": kpis.no_promovidos,
            "tasa_no_promocion": kpis.tasa_no_promocion,
            "retirados": kpis.retirados,
            "tasa_retiro": kpis.tasa_retiro,
            "repitentes": kpis.repitentes,
            "tasa_repitencia": kpis.tasa_repitencia,
            "graduandos": kpis.graduandos,
        },
        "narrativa": explain_kpis(kpis),
    }
