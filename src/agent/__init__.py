"""Módulo del Agente Conversacional Inteligente para EduGuate IA.

Implementa la arquitectura anti-alucinación en 3 pasos:
1. Extracción de intención semántica (Groq LLM / JSON).
2. Cálculo analítico determinista sobre 4.3M de registros (DuckDB).
3. Generación guiada en lenguaje natural para no técnicos (Groq LLM).
"""

from src.agent.engine import EduGuateAgent
from src.agent.schemas import AgentIntent, AgentResponse, QueryCategory

__all__ = ["EduGuateAgent", "AgentIntent", "AgentResponse", "QueryCategory"]
