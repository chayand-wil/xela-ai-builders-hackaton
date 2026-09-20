"""Pruebas unitarias para la fase de Ingesta & ETL (EduGuate IA)."""

from pathlib import Path

import polars as pl
import pytest

from src.ingestion.catalogs import Catalogs
from src.ingestion.cleaner import FINAL_COLUMNS, clean_department_df
from src.ingestion.loader import find_data_sheet


@pytest.fixture(scope="session")
def catalogs() -> Catalogs:
    dict_path = Path("Data/diccionario_de_variables_educaion_formal_2024.xlsx")
    return Catalogs(dict_path)


def test_catalogs_loading(catalogs: Catalogs) -> None:
    """Verifica que los catálogos oficiales carguen correctamente."""
    assert len(catalogs.departamentos_map) == 22
    assert len(catalogs.municipios_map) == 340
    assert catalogs.get_departamento_nombre(1) == "Guatemala"
    assert catalogs.get_departamento_nombre(9) == "Quetzaltenango"
    assert catalogs.get_municipio_nombre("0101") == "Guatemala"
    assert catalogs.get_municipio_nombre("0901") == "Quetzaltenango"


def test_guatemala_prefix_normalization(catalogs: Catalogs) -> None:
    """Verifica que el prefijo '00-' de Guatemala se normalice a '01-' y el municipio sea '0101'."""
    raw_df = pl.DataFrame(
        {
            "Año": [2024, 2024],
            "CodEstablecimiento": ["00-18-0001-43", "00-01-0002-42"],
            "Departamento_F": [1, 1],
            "Depto_mupio": [101, 101],
            "Sector": [1, 2],
            "Área": [1, 2],
            "Sexo": [1, 2],
            "Grado": [1, 2],
            "Nivel": [2, 1],
            "Pueblo_Per": [1, 5],
            "Plan_Est": [1, 1],
            "Jornada_Est": [1, 1],
            "Resultado_F": [1, 1],
            "Repitente": [2, 2],
            "Graduando": [2, 2],
        }
    )

    cleaned = clean_department_df(raw_df, catalogs)

    # Códigos normalizados a 01-
    assert cleaned["codigo_establecimiento"].to_list() == ["01-18-0001-43", "01-01-0002-42"]
    # Municipio derivado correctamente a la Capital (0101)
    assert cleaned["municipio_codigo"].to_list() == ["0101", "0101"]
    assert cleaned["municipio"].to_list() == ["Guatemala", "Guatemala"]
    assert cleaned["departamento"].to_list() == ["Guatemala", "Guatemala"]


def test_standard_municipality_derivation(catalogs: Catalogs) -> None:
    """Verifica que para otros departamentos el municipio se derive de los segmentos 1 y 2."""
    raw_df = pl.DataFrame(
        {
            "Año": [2024],
            "CodEstablecimiento": ["09-01-0005-43"],
            "Departamento_F": [9],
            "Depto_mupio": [901],
            "Sector": [1],
            "Área": [1],
            "Sexo": [1],
            "Grado": [3],
            "Nivel": [2],
            "Pueblo_Per": [1],
            "Plan_Est": [1],
            "Jornada_Est": [1],
            "Resultado_F": [1],
            "Repitente": [2],
            "Graduando": [2],
        }
    )

    cleaned = clean_department_df(raw_df, catalogs)

    assert cleaned["departamento_codigo"][0] == 9
    assert cleaned["departamento"][0] == "Quetzaltenango"
    assert cleaned["municipio_codigo"][0] == "0901"
    assert cleaned["municipio"][0] == "Quetzaltenango"


def test_solola_sheet_detection() -> None:
    """Verifica que en Sololá se detecte 'Sheet1' y no las hojas vacías 'Sheet2' o 'Sheet3'."""
    solola_path = Path("Data/solola_2024.xlsx")
    assert solola_path.exists(), "Archivo de Sololá no encontrado"
    active_sheet = find_data_sheet(solola_path)
    assert active_sheet == "Sheet1"


def test_code_9_preservation(catalogs: Catalogs) -> None:
    """Verifica que el código 9 se conserve como 'Ignorado' y nunca como null."""
    raw_df = pl.DataFrame(
        {
            "Año": [2024],
            "CodEstablecimiento": ["01-02-0001-43"],
            "Departamento_F": [1],
            "Depto_mupio": [102],
            "Sector": [1],
            "Área": [9],
            "Sexo": [9],
            "Grado": [1],
            "Nivel": [9],
            "Pueblo_Per": [9],
            "Plan_Est": [1],
            "Jornada_Est": [9],
            "Resultado_F": [9],
            "Repitente": [9],
            "Graduando": [9],
        }
    )

    cleaned = clean_department_df(raw_df, catalogs)

    assert cleaned["area"][0] == "Ignorado"
    assert cleaned["sexo"][0] == "Ignorado"
    assert cleaned["nivel"][0] == "Ignorado"
    assert cleaned["pueblo_pertenencia"][0] == "Ignorado"
    assert cleaned["jornada"][0] == "Ignorado"
    assert cleaned["resultado"][0] == "Ignorado"
    assert cleaned["repitente"][0] == "Ignorado"
    assert cleaned["graduando"][0] == "Ignorado"
    # Verificar que no hay valores nulos en ninguna columna
    assert cleaned.null_count().sum_horizontal()[0] == 0


def test_schema_integrity(catalogs: Catalogs) -> None:
    """Verifica que las 17 columnas contractuales estén presentes y ordenadas."""
    raw_df = pl.DataFrame(
        {
            "Año": [2024],
            "CodEstablecimiento": ["01-01-0001-43"],
            "Departamento_F": [1],
            "Depto_mupio": [101],
            "Sector": [1],
            "Área": [1],
            "Sexo": [1],
            "Grado": [1],
            "Nivel": [2],
            "Pueblo_Per": [5],
            "Plan_Est": [1],
            "Jornada_Est": [1],
            "Resultado_F": [1],
            "Repitente": [2],
            "Graduando": [2],
        }
    )

    cleaned = clean_department_df(raw_df, catalogs)
    assert cleaned.columns == FINAL_COLUMNS
