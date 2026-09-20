"""Gestor de cliente y configuración de Groq Cloud para EduGuate IA.

Carga la clave de API de forma segura y provee una instancia de cliente lista para inferencia.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _load_env_file() -> None:
    """Carga variables desde el archivo .env local si existe."""
    env_path = Path(".env")
    if not env_path.exists():
        return

    try:
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v
    except Exception as e:
        logger.warning(f"No se pudo leer .env local: {e}")


def get_groq_api_key() -> str | None:
    """Obtiene la clave de API de Groq desde variables de entorno o .env."""
    _load_env_file()
    key = os.getenv("GROQ_API_KEY")
    if key and key.strip():
        return key.strip()

    # Intentar cargar desde st.secrets si está corriendo en Streamlit
    try:
        import streamlit as st

        if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
            return str(st.secrets["GROQ_API_KEY"]).strip()
    except Exception:
        pass

    return None


def get_groq_client() -> Any:
    """Instancia y retorna un cliente de Groq si la clave está configurada."""
    api_key = get_groq_api_key()
    if not api_key:
        logger.warning("GROQ_API_KEY no configurada. El agente operará en modo determinista local.")
        return None

    try:
        from groq import Groq

        return Groq(api_key=api_key)
    except Exception as e:
        logger.error(f"Error al instanciar cliente Groq: {e}")
        return None
