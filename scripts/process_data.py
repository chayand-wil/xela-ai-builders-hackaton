#!/usr/bin/env python3
"""Script principal de orquestación de Ingesta & ETL para Educación Formal 2024.

Flujo:
1. Carga catálogos y diccionarios oficiales.
2. Lee y procesa los 22 archivos departamentales en Data/.
3. Aplica normalización de prefijo '00-', derivación municipal y decodificación.
4. Concatena los 4.3M de registros.
5. Valida contra las cifras de control del INE (Ground Truth).
6. Exporta el dataset procesado a Parquet (data/processed/educacion_formal_2024.parquet).
7. Genera una muestra representativa (data/samples/educacion_formal_sample.parquet).
8. Guarda el reporte de auditoría JSON (data/processed/validation_report.json).
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

# Agregar raíz del proyecto a sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import polars as pl  # noqa: E402
from tqdm import tqdm  # noqa: E402

from src.ingestion.catalogs import Catalogs  # noqa: E402
from src.ingestion.cleaner import clean_department_df  # noqa: E402
from src.ingestion.loader import list_department_files, load_department_file  # noqa: E402
from src.ingestion.validation import save_validation_report, validate_dataset  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("process_data")


def run_pipeline(
    data_dir: Path,
    output_parquet: Path,
    sample_parquet: Path,
    report_json: Path,
    sample_size: int = 10000,
) -> None:
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("INICIANDO PIPELINE DE INGESTA & ETL - EDUGUATE IA 2024")
    logger.info("=" * 60)

    # 1. Cargar catálogos
    dict_file = data_dir / "diccionario_de_variables_educaion_formal_2024.xlsx"
    if not dict_file.exists():
        # Búsqueda insensible a mayúsculas o variaciones
        dict_candidates = list(data_dir.glob("*diccionario*.xlsx"))
        if dict_candidates:
            dict_file = dict_candidates[0]
        else:
            raise FileNotFoundError(f"No se encontró el diccionario en {data_dir}")

    catalogs = Catalogs(dict_file)

    # 2. Listar archivos departamentales
    dept_files = list_department_files(data_dir)
    logger.info(f"Se procesarán {len(dept_files)} archivos departamentales.")

    # 3. Procesar departamento por departamento
    cleaned_dfs: list[pl.DataFrame] = []
    total_raw_rows = 0

    pbar = tqdm(dept_files, desc="Procesando departamentos", unit="archivo")
    for f in pbar:
        t_file = time.time()
        pbar.set_postfix_str(f.stem[:18])
        raw_df = load_department_file(f)
        total_raw_rows += len(raw_df)
        cleaned_df = clean_department_df(raw_df, catalogs)
        cleaned_dfs.append(cleaned_df)
        logger.debug(f"Procesado {f.name}: {len(cleaned_df):,} filas en {time.time() - t_file:.2f}s")

    # 4. Concatenación masiva
    logger.info("Concatenando registros departamentales...")
    df_all = pl.concat(cleaned_dfs, how="vertical")
    logger.info(f"Dataset consolidado: {len(df_all):,} registros con {len(df_all.columns)} columnas.")

    # 5. Validación contra Ground Truth
    logger.info("Ejecutando validaciones estadísticas...")
    report = validate_dataset(df_all)

    print("\n" + "=" * 60)
    print("REPORTE DE VALIDACIÓN Y CONTROL (GROUND TRUTH)")
    print("=" * 60)
    print(f"Total Registros Obtenidos: {report['total_registros_obtenido']:,}")
    print(f"Total Registros Esperados: {report['total_registros_esperado']:,}")
    print(f"Diferencia: {report['diferencia_total']}")
    print(f"Municipios en Guatemala: {report['checks']['municipios_guatemala']['obtenido']} (Esperado: 17)")
    print(f"Municipios Nacionales con Datos: {report['checks']['municipios_nacionales']['obtenido']} (Esperado: ≈ 340)")
    print("\nDistribución por Sector (%):")
    for sec, pct in report["checks"]["sector"]["obtenido"].items():
        exp = report["checks"]["sector"]["esperado"].get(sec, "N/A")
        print(f"  - {sec:15s}: {pct:5.1f}% (esperado: {exp}%)")

    print("\nDistribución por Área (%):")
    for a, pct in report["checks"]["area"]["obtenido"].items():
        exp = report["checks"]["area"]["esperado"].get(a, "N/A")
        print(f"  - {a:15s}: {pct:5.1f}% (esperado: {exp}%)")

    print("\nDistribución por Sexo (%):")
    for s, pct in report["checks"]["sexo"]["obtenido"].items():
        exp = report["checks"]["sexo"]["esperado"].get(s, "N/A")
        print(f"  - {s:15s}: {pct:5.1f}% (esperado: {exp}%)")

    print("\nDistribución por Nivel (%):")
    for n, pct in report["checks"]["nivel"]["obtenido"].items():
        exp = report["checks"]["nivel"]["esperado"].get(n, "N/A")
        print(f"  - {n:15s}: {pct:5.1f}% (esperado: {exp}%)")

    print("\nDistribución por Resultado (%):")
    for r, pct in report["checks"]["resultado"]["obtenido"].items():
        exp = report["checks"]["resultado"]["esperado"].get(r, "N/A")
        print(f"  - {r:15s}: {pct:5.1f}% (esperado: {exp}%)")

    print(f"\nEstado global de validación: {'APROBADO (PASS)' if report['overall_passed'] else 'FALLÓ (FAIL)'}")
    print("=" * 60 + "\n")

    # 6. Guardar reporte de validación
    save_validation_report(report, report_json)

    # 7. Exportar dataset procesado a Parquet
    logger.info(f"Exportando dataset completo a Parquet en {output_parquet}...")
    output_parquet.parent.mkdir(parents=True, exist_ok=True)
    df_all.write_parquet(output_parquet, compression="zstd")
    file_size_mb = output_parquet.stat().st_size / (1024 * 1024)
    logger.info(f"Parquet guardado exitosamente: {file_size_mb:.2f} MB")

    # 8. Generar y exportar muestra estratificada/representativa
    logger.info(f"Generando muestra de {sample_size:,} registros en {sample_parquet}...")
    sample_parquet.parent.mkdir(parents=True, exist_ok=True)
    # Muestra con semilla fija para reproducibilidad exacta
    sample_df = df_all.sample(n=min(sample_size, len(df_all)), seed=42)
    sample_df.write_parquet(sample_parquet, compression="zstd")
    logger.info(f"Muestra guardada: {len(sample_df):,} registros.")

    elapsed = time.time() - start_time
    logger.info(f"Pipeline completado exitosamente en {elapsed:.2f} segundos ({elapsed / 60:.2f} minutos).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline ETL de Educación Formal 2024")
    parser.add_argument("--data-dir", type=Path, default=Path("Data"), help="Directorio con archivos Excel")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/educacion_formal_2024.parquet"),
        help="Ruta del Parquet consolidado",
    )
    parser.add_argument(
        "--sample-output",
        type=Path,
        default=Path("data/samples/educacion_formal_sample.parquet"),
        help="Ruta del Parquet de muestra",
    )
    parser.add_argument(
        "--report-output",
        type=Path,
        default=Path("data/processed/validation_report.json"),
        help="Ruta del reporte JSON de validación",
    )
    parser.add_argument("--sample-size", type=int, default=10000, help="Tamaño de la muestra")

    args = parser.parse_args()
    run_pipeline(
        data_dir=args.data_dir,
        output_parquet=args.output,
        sample_parquet=args.sample_output,
        report_json=args.report_output,
        sample_size=args.sample_size,
    )


if __name__ == "__main__":
    main()
