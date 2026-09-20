"""Módulo para la carga robusta y validada de archivos Excel departamentales.

Maneja:
- Detección inteligente de hojas con datos reales (resuelve hojas vacías en Sololá).
- Verificación del contrato de 15 columnas obligatorias.
- Validación de conteo esperado de registros por departamento.
- Lectura de alto rendimiento mediante el motor 'calamine' en Polars.
"""

from __future__ import annotations

import logging
from pathlib import Path

import fastexcel
import polars as pl

logger = logging.getLogger(__name__)

# Contrato estricto de las 15 columnas originales
EXPECTED_COLUMNS: list[str] = [
    "Año",
    "CodEstablecimiento",
    "Departamento_F",
    "Depto_mupio",
    "Sector",
    "Área",
    "Sexo",
    "Grado",
    "Nivel",
    "Pueblo_Per",
    "Plan_Est",
    "Jornada_Est",
    "Resultado_F",
    "Repitente",
    "Graduando",
]

# Conteos oficiales de control por departamento según convocatoria INE 2024
EXPECTED_DEPARTMENTS_ROWS: dict[str, int] = {
    "alta_verapaz": 391085,
    "baja_verapaz": 81736,
    "chimaltenango": 166965,
    "chiquimula": 127409,
    "el_progreso": 49803,
    "el-progreso": 49803,
    "escuintla": 207618,
    "guatemala": 863879,
    "huehuetenango": 316771,
    "izabal": 120326,
    "jalapa": 99625,
    "jutiapa": 134571,
    "peten": 169629,
    "quetzaltenango": 232627,
    "quiche": 268998,
    "retalhuleu": 98128,
    "sacatepequez": 91552,
    "san_marcos": 303565,
    "santa_rosa": 108264,
    "solola": 122831,
    "suchitepequez": 159287,
    "totonicapan": 113139,
    "zacapa": 71079,
}


def list_department_files(data_dir: str | Path) -> list[Path]:
    """Encuentra y retorna los 22 archivos departamentales en data_dir, excluyendo el diccionario."""
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"El directorio {data_dir} no existe.")

    files: list[Path] = []
    for f in sorted(data_path.glob("*.xlsx")):
        # Ignorar archivos de diccionario o temporales
        if "diccionario" in f.name.lower() or f.name.startswith("~$") or f.name.startswith("."):
            continue
        files.append(f)

    if len(files) != 22:
        logger.warning(f"Se esperaban 22 archivos departamentales, se encontraron {len(files)}.")

    return files


def find_data_sheet(file_path: Path) -> str:
    """Detecta de manera robusta el nombre de la hoja que contiene los datos en un archivo Excel."""
    excel = fastexcel.read_excel(file_path)
    sheet_names = excel.sheet_names

    if len(sheet_names) == 1:
        return sheet_names[0]

    # Para libros con múltiples hojas (caso Sololá), inspeccionamos cada hoja
    for s_name in sheet_names:
        try:
            sheet = excel.load_sheet_by_name(s_name)
            # Descartar hojas vacías o con altura anómala (overflow en fastexcel para hojas vacías)
            if 0 < sheet.total_height < 5_000_000:
                logger.info(f"Hoja válida encontrada en {file_path.name}: '{s_name}' ({sheet.total_height} filas)")
                return s_name
        except Exception as e:
            logger.debug(f"Error al inspeccionar hoja {s_name} en {file_path.name}: {e}")

    # Fallback: devolver la primera hoja
    return sheet_names[0]


def get_department_key(file_path: Path) -> str:
    """Normaliza el nombre del archivo para cotejar con EXPECTED_DEPARTMENTS_ROWS."""
    stem = file_path.stem.lower()
    for suffix in ["_2024", "-2024", "_formal"]:
        stem = stem.replace(suffix, "")
    stem = stem.replace("-", "_").replace(" ", "_")
    return stem


def load_department_file(file_path: Path) -> pl.DataFrame:
    """Carga un archivo departamental validando esquema, hoja y conteo preliminar."""
    if not file_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

    sheet_name = find_data_sheet(file_path)

    try:
        # Usar Polars con motor calamine (alto rendimiento en Rust)
        df = pl.read_excel(
            file_path,
            sheet_name=sheet_name,
            engine="calamine",
            schema_overrides={
                "Año": pl.Int32,
                "CodEstablecimiento": pl.Utf8,
                "Departamento_F": pl.Int32,
                "Depto_mupio": pl.Int32,
                "Sector": pl.Int32,
                "Área": pl.Int32,
                "Sexo": pl.Int32,
                "Grado": pl.Int32,
                "Nivel": pl.Int32,
                "Pueblo_Per": pl.Int32,
                "Plan_Est": pl.Int32,
                "Jornada_Est": pl.Int32,
                "Resultado_F": pl.Int32,
                "Repitente": pl.Int32,
                "Graduando": pl.Int32,
            },
        )
    except Exception as e:
        logger.error(f"Error al leer {file_path.name} con calamine: {e}")
        raise

    # 1. Validación de esquema
    missing_cols = set(EXPECTED_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"El archivo {file_path.name} no cumple el contrato de columnas. Faltan: {missing_cols}"
        )

    # 2. Validación de conteo esperado por departamento
    dept_key = get_department_key(file_path)
    expected_rows = EXPECTED_DEPARTMENTS_ROWS.get(dept_key)
    if expected_rows is not None and len(df) != expected_rows:
        logger.warning(
            f"Conteo anómalo en {file_path.name} ({dept_key}): se esperaban {expected_rows} filas, "
            f"se obtuvieron {len(df)} filas."
        )

    logger.debug(f"Cargado exitosamente {file_path.name}: {len(df)} registros.")
    return df
