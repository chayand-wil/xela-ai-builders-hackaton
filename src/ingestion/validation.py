"""Módulo de validación estadística y auditoría de calidad contra Ground Truth oficial.

Verifica:
1. Total de registros nacional == 4,298,887.
2. Total de municipios en el departamento de Guatemala == 17.
3. Total de municipios con datos a nivel nacional ≈ 340.
4. Distribuciones oficiales por Sector, Área, Sexo, Nivel y Resultado.
5. Emite reporte formal de validación en JSON para auditoría.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import polars as pl

logger = logging.getLogger(__name__)

# Cifras de control oficiales estipuladas en hackaton.md
GROUND_TRUTH: dict[str, Any] = {
    "total_registros": 4298887,
    "municipios_guatemala": 17,
    "sector": {
        "Público": 74.7,
        "Privado": 20.9,
        "Cooperativa": 4.0,
        "Municipal": 0.3,
    },
    "area": {
        "Rural": 61.4,
        "Urbana": 38.6,
    },
    "sexo": {
        "Hombre": 50.7,
        "Mujer": 49.3,
    },
    "nivel": {
        "Primaria": 56.4,
        "Básico": 17.8,
        "Preprimaria": 17.1,
        "Diversificado": 8.5,
    },
    "resultado": {
        "Promovido": 85.2,
        "No promovido": 9.2,
        "Retirado": 5.5,
    },
}


def compute_distribution(df: pl.DataFrame, col_name: str) -> dict[str, float]:
    """Calcula la distribución porcentual de una columna."""
    total = len(df)
    if total == 0:
        return {}
    counts = df.group_by(col_name).len()
    dist: dict[str, float] = {}
    for row in counts.iter_rows():
        val, count = str(row[0]), row[1]
        dist[val] = round((count / total) * 100, 2)
    return dist


def validate_dataset(df: pl.DataFrame) -> dict[str, Any]:
    """Ejecuta la suite completa de validaciones estadísticas contra el dataset procesado."""
    total_records = len(df)
    report: dict[str, Any] = {
        "total_registros_obtenido": total_records,
        "total_registros_esperado": GROUND_TRUTH["total_registros"],
        "diferencia_total": total_records - GROUND_TRUTH["total_registros"],
        "passed_total": total_records == GROUND_TRUTH["total_registros"],
        "checks": {},
    }

    # 1. Validación de municipios de Guatemala
    gt_dept = df.filter(pl.col("departamento_codigo") == 1)
    mupios_gt = sorted(gt_dept["municipio"].unique().to_list())
    report["checks"]["municipios_guatemala"] = {
        "obtenido": len(mupios_gt),
        "esperado": 17,
        "passed": len(mupios_gt) == 17,
        "lista_municipios": mupios_gt,
    }

    # 2. Total municipios nacionales con datos
    all_mupios = sorted(df["municipio_codigo"].unique().to_list())
    report["checks"]["municipios_nacionales"] = {
        "obtenido": len(all_mupios),
        "esperado": "≈ 340",
        "passed": 335 <= len(all_mupios) <= 345,
    }

    # 3. Distribución por Sector
    sector_dist = compute_distribution(df, "sector")
    report["checks"]["sector"] = {
        "obtenido": sector_dist,
        "esperado": GROUND_TRUTH["sector"],
    }

    # 4. Distribución por Área
    area_dist = compute_distribution(df, "area")
    report["checks"]["area"] = {
        "obtenido": area_dist,
        "esperado": GROUND_TRUTH["area"],
    }

    # 5. Distribución por Sexo
    sexo_dist = compute_distribution(df, "sexo")
    report["checks"]["sexo"] = {
        "obtenido": sexo_dist,
        "esperado": GROUND_TRUTH["sexo"],
    }

    # 6. Distribución por Nivel
    nivel_dist = compute_distribution(df, "nivel")
    report["checks"]["nivel"] = {
        "obtenido": nivel_dist,
        "esperado": GROUND_TRUTH["nivel"],
    }

    # 7. Distribución por Resultado (agrupando Retirado y Retirado definitivo para comparar con 5.5%)
    res_df = df.with_columns(
        pl.when(pl.col("resultado").is_in(["Retirado", "Retirado definitivo"]))
        .then(pl.lit("Retirado"))
        .otherwise(pl.col("resultado"))
        .alias("resultado_eval")
    )
    res_dist = compute_distribution(res_df, "resultado_eval")
    report["checks"]["resultado"] = {
        "obtenido": res_dist,
        "esperado": GROUND_TRUTH["resultado"],
    }

    # Evaluación global
    all_passed = (
        report["passed_total"]
        and report["checks"]["municipios_guatemala"]["passed"]
        and report["checks"]["municipios_nacionales"]["passed"]
    )
    report["overall_passed"] = all_passed

    return report


def save_validation_report(report: dict[str, Any], output_path: str | Path) -> None:
    """Guarda el reporte de validación en formato JSON legible."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    logger.info(f"Reporte de validación guardado en {path}")
