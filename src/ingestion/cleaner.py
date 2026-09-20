"""Módulo de limpieza, normalización y transformación de datos educativos.

Aplica:
- Normalización del prefijo '00-' de Guatemala a '01-'.
- Derivación correcta del municipio:
    * Si el código inicia con '00-', se asigna al municipio '0101' (Guatemala Capital).
    * En cualquier otro caso, se deriva de los primeros dos segmentos (DD + MM -> 4 dígitos).
- Decodificación completa de códigos a etiquetas legibles (Sector, Área, Sexo, Nivel, etc.).
- Preservación explícita del código 9 como 'Ignorado'.
- Tipado estricto y optimizado según el contrato acordado en el plan de arquitectura.
"""

from __future__ import annotations

import logging

import polars as pl

from src.ingestion.catalogs import Catalogs

logger = logging.getLogger(__name__)

FINAL_COLUMNS: list[str] = [
    "anio",
    "codigo_establecimiento",
    "departamento_codigo",
    "departamento",
    "municipio_codigo",
    "municipio",
    "sector",
    "area",
    "sexo",
    "grado",
    "nivel",
    "pueblo_pertenencia",
    "plan_estudios",
    "jornada",
    "resultado",
    "repitente",
    "graduando",
]


def clean_department_df(raw_df: pl.DataFrame, catalogs: Catalogs) -> pl.DataFrame:
    """Limpia, decodifica y normaliza un DataFrame departamental crudo."""
    # 1. Normalización de CodEstablecimiento y derivación territorial
    # Si empieza con '00-', normalizamos a '01-' en el código
    # y asignamos municipio '0101' (Guatemala Capital)
    cod_raw = pl.col("CodEstablecimiento")

    is_capital_00 = cod_raw.str.starts_with("00-")
    cod_norm = (
        pl.when(is_capital_00)
        .then(pl.concat_str([pl.lit("01-"), cod_raw.str.slice(3)]))
        .otherwise(cod_raw)
        .alias("codigo_establecimiento")
    )

    # Extraer municipio_codigo (4 dígitos)
    mupio_code = (
        pl.when(is_capital_00)
        .then(pl.lit("0101"))
        .otherwise(pl.concat_str([cod_raw.str.slice(0, 2), cod_raw.str.slice(3, 2)]))
        .alias("municipio_codigo")
    )

    # Departamento código (Int8)
    dept_code = pl.col("Departamento_F").cast(pl.Int8).alias("departamento_codigo")

    # Mapeo de diccionarios con reemplazo estricto/seguro
    # polars replace soporta dict de Python directamente
    sector_col = pl.col("Sector").replace_strict(catalogs.sector_map, default="Ignorado").alias("sector")
    area_col = pl.col("Área").replace_strict(catalogs.area_map, default="Ignorado").alias("area")
    sexo_col = pl.col("Sexo").replace_strict(catalogs.sexo_map, default="Ignorado").alias("sexo")
    nivel_col = pl.col("Nivel").replace_strict(catalogs.nivel_map, default="Ignorado").alias("nivel")
    pueblo_col = (
        pl.col("Pueblo_Per").replace_strict(catalogs.pueblo_map, default="Ignorado").alias("pueblo_pertenencia")
    )
    plan_col = pl.col("Plan_Est").replace_strict(catalogs.plan_est_map, default="Ignorado").alias("plan_estudios")
    jornada_col = pl.col("Jornada_Est").replace_strict(catalogs.jornada_map, default="Ignorado").alias("jornada")
    resultado_col = pl.col("Resultado_F").replace_strict(catalogs.resultado_map, default="Ignorado").alias("resultado")
    repitente_col = pl.col("Repitente").replace_strict(catalogs.repitente_map, default="Ignorado").alias("repitente")
    graduando_col = pl.col("Graduando").replace_strict(catalogs.graduando_map, default="Ignorado").alias("graduando")

    # Transformación inicial
    df_transformed = raw_df.select(
        [
            pl.col("Año").cast(pl.Int16).alias("anio"),
            cod_norm,
            dept_code,
            mupio_code,
            sector_col,
            area_col,
            sexo_col,
            pl.col("Grado").cast(pl.Int8).alias("grado"),
            nivel_col,
            pueblo_col,
            plan_col,
            jornada_col,
            resultado_col,
            repitente_col,
            graduando_col,
        ]
    )

    # Asignar nombres textuales de departamento y municipio
    dept_map_expr = (
        pl.col("departamento_codigo")
        .replace_strict(catalogs.departamentos_map, default="Desconocido")
        .alias("departamento")
    )

    mupio_map_expr = (
        pl.col("municipio_codigo").replace_strict(catalogs.municipios_map, default="Desconocido").alias("municipio")
    )

    df_final = df_transformed.with_columns(
        [
            dept_map_expr,
            mupio_map_expr,
        ]
    ).select(FINAL_COLUMNS)

    return df_final
