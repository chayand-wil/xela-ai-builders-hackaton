"""Módulo de catálogos y diccionarios de variables para Educación Formal 2024.

Provee los mapeos oficiales de códigos a etiquetas para:
- Sector, Área, Sexo, Nivel, Pueblo de Pertenencia, Plan de Estudio, Jornada,
  Resultado Final, Repitente y Graduando.
- Departamentos (1-22) y Municipios (340 municipios por código de 4 dígitos).
"""

from __future__ import annotations

import logging
from pathlib import Path

import polars as pl

logger = logging.getLogger(__name__)

# Catálogos oficiales extraídos del diccionario INE 2024
SECTOR_MAP: dict[int, str] = {
    1: "Público",
    2: "Privado",
    3: "Municipal",
    4: "Cooperativa",
}

AREA_MAP: dict[int, str] = {
    1: "Urbana",
    2: "Rural",
    9: "Ignorado",
}

SEXO_MAP: dict[int, str] = {
    1: "Hombre",
    2: "Mujer",
    9: "Ignorado",
}

NIVEL_MAP: dict[int, str] = {
    1: "Preprimaria",
    2: "Primaria",
    3: "Básico",
    4: "Diversificado",
    5: "Primaria de adultos",
    9: "Ignorado",
}

PUEBLO_MAP: dict[int, str] = {
    1: "Maya",
    2: "Garífuna",
    3: "Xinka",
    4: "Afrodescendiente/Creole/Afromestizo",
    5: "Ladino/Mestizo",
    6: "Extranjero",
    9: "Ignorado",
}

PLAN_EST_MAP: dict[int, str] = {
    1: "Diario",
    2: "Fin de semana",
    3: "Virtual a distancia",
    4: "Semipresencial",
    5: "Mixto",
}

JORNADA_MAP: dict[int, str] = {
    1: "Matutina",
    2: "Vespertina",
    3: "Nocturna",
    4: "Doble",
    5: "Intermedia",
    9: "Ignorado",
}

RESULTADO_MAP: dict[int, str] = {
    1: "Promovido",
    2: "Vigente",
    3: "Retirado",
    4: "Retirado definitivo",
    5: "No promovido",
    9: "Ignorado",
}

REPITENTE_MAP: dict[int, str] = {
    1: "Sí",
    2: "No",
    9: "Ignorado",
}

GRADUANDO_MAP: dict[int, str] = {
    1: "Sí es graduando",
    2: "No es graduando",
    9: "Ignorado",
}

DEPARTAMENTOS_MAP: dict[int, str] = {
    1: "Guatemala",
    2: "El Progreso",
    3: "Sacatepéquez",
    4: "Chimaltenango",
    5: "Escuintla",
    6: "Santa Rosa",
    7: "Sololá",
    8: "Totonicapán",
    9: "Quetzaltenango",
    10: "Suchitepéquez",
    11: "Retalhuleu",
    12: "San Marcos",
    13: "Huehuetenango",
    14: "Quiché",
    15: "Baja Verapaz",
    16: "Alta Verapaz",
    17: "Petén",
    18: "Izabal",
    19: "Zacapa",
    20: "Chiquimula",
    21: "Jalapa",
    22: "Jutiapa",
}

# Límites válidos de grado por nivel según la estructura oficial
GRADO_LIMITS_POR_NIVEL: dict[int, tuple[int, int]] = {
    1: (0, 6),  # Preprimaria
    2: (1, 6),  # Primaria
    3: (1, 3),  # Básico
    4: (4, 7),  # Diversificado
    5: (1, 4),  # Primaria de adultos
}


class Catalogs:
    """Administrador centralizado de catálogos y diccionarios geográficos."""

    def __init__(self, dictionary_path: str | Path | None = None) -> None:
        self.sector_map = dict(SECTOR_MAP)
        self.area_map = dict(AREA_MAP)
        self.sexo_map = dict(SEXO_MAP)
        self.nivel_map = dict(NIVEL_MAP)
        self.pueblo_map = dict(PUEBLO_MAP)
        self.plan_est_map = dict(PLAN_EST_MAP)
        self.jornada_map = dict(JORNADA_MAP)
        self.resultado_map = dict(RESULTADO_MAP)
        self.repitente_map = dict(REPITENTE_MAP)
        self.graduando_map = dict(GRADUANDO_MAP)
        self.departamentos_map = dict(DEPARTAMENTOS_MAP)
        self.municipios_map: dict[str, str] = {}

        if dictionary_path and Path(dictionary_path).exists():
            self.load_from_excel(Path(dictionary_path))

    def load_from_excel(self, file_path: Path) -> None:
        """Lee y actualiza los catálogos directamente desde el archivo Excel oficial."""
        logger.info(f"Cargando catálogos desde {file_path}...")
        try:
            # 1. Departamentos y municipios
            df_geo = pl.read_excel(
                file_path,
                sheet_name="Departamentos y municipios",
                engine="calamine",
            )
            current_category = None
            for row in df_geo.iter_rows():
                val, code, label = row[0], row[1], row[2]
                if val == "Valor" or code == "Código" or (val is None and code is None and label is None):
                    continue
                if val is not None and str(val).strip():
                    current_category = str(val).strip()
                if current_category == "Departamentos" and code is not None and label is not None:
                    try:
                        self.departamentos_map[int(code)] = str(label).strip()
                    except ValueError:
                        pass
                elif current_category == "Municipios" and code is not None and label is not None:
                    # Código municipal siempre en formato de 4 dígitos ('0101', '0901', etc.)
                    code_str = str(code).strip().zfill(4)
                    self.municipios_map[code_str] = str(label).strip()

            logger.info(
                f"Catálogos cargados con éxito: {len(self.departamentos_map)} departamentos, "
                f"{len(self.municipios_map)} municipios."
            )
        except Exception as e:
            logger.error(f"Error al cargar catálogos desde Excel: {e}")
            raise

    def get_departamento_nombre(self, code: int) -> str:
        return self.departamentos_map.get(code, f"Desconocido ({code})")

    def get_municipio_nombre(self, code_4_digits: str) -> str:
        return self.municipios_map.get(code_4_digits, f"Municipio {code_4_digits}")
