"""Rutas del Parquet y variables de entorno de EduGuate IA."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")

_TRUTHY = {"1", "true", "yes", "on", "si", "sí"}


def _as_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in _TRUTHY


def _resolve(path_value: str) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def use_sample() -> bool:
    return _as_bool(os.getenv("EDUGUATE_USE_SAMPLE"))


def get_parquet_path() -> str:
    """Ruta absoluta del Parquet activo (muestra o dataset completo)."""
    if use_sample():
        raw = os.getenv("EDUGUATE_SAMPLE_PATH", "Data/samples/educacion_formal_sample.parquet")
    else:
        raw = os.getenv("EDUGUATE_PARQUET_PATH", "Data/processed/educacion_formal_2024.parquet")
    path = _resolve(raw)
    if not path.exists():
        raise FileNotFoundError(
            f"No se encontró el Parquet en {path}. "
            "Revisa EDUGATE_PARQUET_PATH / EDUGATE_SAMPLE_PATH o genera los datos."
        )
    return path.resolve().as_posix()
