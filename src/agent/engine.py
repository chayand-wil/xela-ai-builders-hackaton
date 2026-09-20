"""Orquestador principal del Agente Conversacional EduGuate IA.

Integra la extracción semántica mediante Groq LLM, el cálculo matemático determinista
con DuckDB y la generación guiada con guardrails contra alucinaciones.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from src.agent.client import get_groq_client
from src.agent.prompts import INTENT_EXTRACTION_SYSTEM_PROMPT, RESPONSE_GENERATION_SYSTEM_PROMPT
from src.agent.schemas import AgentIntent, AgentResponse, QueryCategory
from src.agent.tools import execute_intent
from src.analytics.queries import AnalyticsEngine

logger = logging.getLogger(__name__)

# Palabras clave para guardrail de consultas fuera de alcance
OUT_OF_SCOPE_KEYWORDS = [
    "sueldo",
    "salario",
    "cuanto gana",
    "cuánto gana",
    "presupuesto",
    "gasto publico",
    "dinero",
    "computadora",
    "pupitre",
    "edificio",
    "infraestructura",
    "2015",
    "2018",
    "2020",
    "2021",
    "2022",
    "2023",
    "honduras",
    "el salvador",
    "mexico",
]


class EduGuateAgent:
    """Agente conversacional en lenguaje natural con arquitectura anti-alucinación."""

    def __init__(self, engine: AnalyticsEngine | None = None) -> None:
        self.engine = engine or AnalyticsEngine()
        self.client = get_groq_client()
        self.model_name = "groq/compound-mini"

    def _fallback_intent_parser(self, query: str) -> AgentIntent:
        """Clasificador heurístico determinista si la API de Groq no estuviese disponible."""
        q_lower = query.lower()

        # Saludo
        if any(w in q_lower for w in ["hola", "buenos días", "buenas tardes", "ayuda", "qué puedes hacer"]):
            return AgentIntent(
                categoria=QueryCategory.GREETING,
                pregunta_normalizada=query,
            )

        # Fuera de alcance
        if any(w in q_lower for w in OUT_OF_SCOPE_KEYWORDS):
            return AgentIntent(
                categoria=QueryCategory.OUT_OF_SCOPE,
                pregunta_normalizada=query,
                razon_fuera_de_alcance=(
                    "El Censo de Educación Formal 2024 registra matrícula, sector, área, nivel y resultados "
                    "terminales, pero no contiene información sobre sueldos, presupuestos, infraestructura ni otros."
                ),
            )

        # Análisis interpretativo
        keywords_analisis = ["por qué", "por que", "conclusión", "conclusiones", "análisis", "interpretación"]
        if any(w in q_lower for w in keywords_analisis):
            return AgentIntent(
                categoria=QueryCategory.ANALYSIS_QUERY,
                pregunta_normalizada=query,
            )

        # Consulta de datos (DATA_QUERY)
        filtros: dict[str, Any] = {}
        for depto in self.engine.get_departments_list():
            if depto.lower() in q_lower:
                filtros["departamento"] = depto
                break

        if "rural" in q_lower:
            filtros["area"] = "Rural"
        elif "urbana" in q_lower:
            filtros["area"] = "Urbana"

        if "público" in q_lower or "publico" in q_lower or "oficial" in q_lower:
            filtros["sector"] = "Oficial"
        elif "privado" in q_lower or "colegio" in q_lower:
            filtros["sector"] = "Privado"

        if "primaria" in q_lower:
            filtros["nivel"] = "Primaria"
        elif "básico" in q_lower or "basico" in q_lower:
            filtros["nivel"] = "Básico"
        elif "diversificado" in q_lower:
            filtros["nivel"] = "Diversificado"

        metrica = "matricula"
        es_rank = False
        if any(w in q_lower for w in ["deserción", "desercion", "retiro", "abandono"]):
            metrica = "tasa_retiro"
            es_rank = True
        elif any(w in q_lower for w in ["aprobación", "aprobacion", "promoción", "promocion"]):
            metrica = "tasa_promocion"
            es_rank = True
        elif any(w in q_lower for w in ["reprobación", "reprobacion", "no promovido"]):
            metrica = "tasa_no_promocion"
            es_rank = True

        return AgentIntent(
            categoria=QueryCategory.DATA_QUERY,
            filtros=filtros,
            metrica=metrica,
            es_ranking=es_rank,
            pregunta_normalizada=query,
        )

    def extract_intent(self, query: str) -> AgentIntent:
        """Extrae la intención estructurada de la pregunta mediante Groq (o fallback)."""
        # Guardrail inmediato para consultas evidentemente fuera de alcance
        q_lower = query.lower()
        if any(w in q_lower for w in OUT_OF_SCOPE_KEYWORDS):
            return AgentIntent(
                categoria=QueryCategory.OUT_OF_SCOPE,
                pregunta_normalizada=query,
                razon_fuera_de_alcance=(
                    "El Censo de Educación Formal 2024 del INE recopila información sobre estudiantes, "
                    "establecimientos, matrícula, sectores, áreas y resultados académicos, pero NO incluye datos "
                    "sobre sueldos, presupuestos financieros, infraestructura escolar ni de otros ciclos escolares."
                ),
            )

        if not self.client:
            return self._fallback_intent_parser(query)

        try:
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": INTENT_EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": query},
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
            )
            raw_content = resp.choices[0].message.content or "{}"
            parsed = json.loads(raw_content)
            return AgentIntent(**parsed)
        except Exception as e:
            logger.warning(f"Error en extracción LLM con Groq ({e}). Usando clasificador local.")
            return self._fallback_intent_parser(query)

    def generate_response(
        self,
        query: str,
        intent: AgentIntent,
        calculated_data: dict[str, Any],
    ) -> str:
        """Genera la respuesta final en lenguaje natural con guardrails anti-alucinación."""
        if not self.client:
            # Generación determinista de respaldo sin LLM
            if intent.categoria == QueryCategory.GREETING:
                return (
                    "¡Hola! 👋 Soy **EduGuate IA**, tu asistente analítico para la Educación Formal en Guatemala. "
                    "Puedo responder preguntas sobre matrículas, tasas de aprobación, deserción escolar y brechas "
                    "en los 22 departamentos y 340 municipios del Censo 2024."
                )
            if intent.categoria == QueryCategory.OUT_OF_SCOPE:
                return (
                    f"⚠️ **Consulta fuera de alcance:** {calculated_data.get('razon')}\n\n"
                    "El dataset oficial del Censo 2024 solo contiene información sobre alumnos matriculados, "
                    "sectores, áreas geográficas, niveles y resultados terminales de promoción o retiro."
                )
            return calculated_data.get("narrativa") or "Consulta analítica procesada exitosamente."

        try:
            prompt_context = (
                f"Pregunta del usuario: {query}\n\n"
                f"Categoría identificada: {intent.categoria.value}\n\n"
                f"DATOS CALCULADOS POR DUCKDB (USA EXCLUSIVAMENTE ESTAS CIFRAS):\n"
                f"{json.dumps(calculated_data, ensure_ascii=False, indent=2)}"
            )

            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": RESPONSE_GENERATION_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_context},
                ],
                temperature=0.2,
            )
            return resp.choices[0].message.content or "No se pudo generar una respuesta."
        except Exception as e:
            logger.warning(f"Error en generación con Groq ({e}). Usando narrativa de respaldo.")
            return calculated_data.get("narrativa") or "Error al procesar la respuesta."

    def ask(self, user_query: str) -> AgentResponse:
        """Punto de entrada principal: atiende una consulta en lenguaje natural con el pipeline anti-alucinación."""
        start_time = time.perf_counter()

        # 1. Extracción de intención
        intent = self.extract_intent(user_query)

        # 2. Resolución analítica determinista (DuckDB)
        calc_data = execute_intent(intent, self.engine)

        # 3. Generación guiada con guardrails
        text_response = self.generate_response(user_query, intent, calc_data)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        mode_str = "Groq LPU (Llama 3.3)" if self.client else "Motor Determinista Local"

        return AgentResponse(
            texto=text_response,
            categoria=intent.categoria,
            cifras_calculadas=calc_data,
            fuente_datos=["educacion_formal_2024.parquet", "DuckDB In-Memory Engine"],
            latencia_ms=round(elapsed_ms, 1),
            modo_ia=mode_str,
        )
