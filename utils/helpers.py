"""
helpers.py — Utilidades generales para los tests de Orion Contact Center
"""
import os
import csv
import pandas as pd
from datetime import datetime


def get_timestamp() -> str:
    """Retorna timestamp actual para nombrar archivos."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_csv_report(filepath: str) -> pd.DataFrame:
    """
    Leer un reporte CSV exportado desde Orion Contact Center.
    Retorna un DataFrame de pandas para validación de datos.
    """
    return pd.read_csv(filepath, encoding="utf-8-sig")


def read_excel_report(filepath: str, sheet_name: str = 0) -> pd.DataFrame:
    """
    Leer un reporte Excel exportado desde Orion Contact Center.
    Retorna un DataFrame de pandas para validación de datos.
    """
    return pd.read_excel(filepath, sheet_name=sheet_name)


def assert_report_not_empty(df: pd.DataFrame, report_name: str):
    """Verificar que un reporte exportado no está vacío."""
    assert not df.empty, f"El reporte '{report_name}' está vacío"


def assert_columns_exist(df: pd.DataFrame, expected_columns: list, report_name: str):
    """Verificar que las columnas esperadas existen en el reporte exportado."""
    for col in expected_columns:
        assert col in df.columns, \
            f"Columna '{col}' no encontrada en '{report_name}'. Columnas: {list(df.columns)}"


def get_downloads_path() -> str:
    """Retorna la ruta de la carpeta de descargas."""
    return os.path.join(os.path.expanduser("~"), "Downloads")
