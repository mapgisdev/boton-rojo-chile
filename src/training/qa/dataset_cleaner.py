"""
src/training/qa/dataset_cleaner.py — Pipeline de ingesta, estandarización y QA/QC del consolidado de incendios.

Lee directamente desde `insumos/` de forma no destructiva y genera `data/derived/incendios_qa.parquet`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import h3
import numpy as np
import pandas as pd

from src.shared.time_utils import TZ_EASTER, TZ_SANTIAGO, TZ_UTC, is_in_br_window, to_local, to_utc

ROOT = Path(__file__).resolve().parents[3]
INPUT_CSV = ROOT / "insumos" / "Consolidado_incendios_2014_2024_temporada.csv"
DERIVED_DIR = ROOT / "data" / "derived"
DERIVED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PARQUET = DERIVED_DIR / "incendios_qa.parquet"

TRAIN_SEASONS = {
    "2014 al 2015", "2015 al 2016", "2016 al 2017",
    "2017 al 2018", "2018 al 2019", "2019 al 2020", "2020 al 2021"
}
VAL_SEASONS = {"2021 al 2022"}
TEST_SEASONS = {"2022 al 2023", "2023 al 2024"}


def parse_float(val: Any) -> float:
    """Parsea números formateados en español (coma decimal) o flotantes estándar."""
    if pd.isna(val) or val is None or val == "":
        return np.nan
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return np.nan


def parse_datetime_with_tz(dt_str: Any, is_easter_island: bool = False) -> Optional[pd.Timestamp]:
    """Parsea un string de fecha/hora y le asigna la zona horaria IANA correspondiente."""
    if pd.isna(dt_str) or not dt_str:
        return None
    try:
        ts = pd.to_datetime(dt_str)
        tz = TZ_EASTER if is_easter_island else TZ_SANTIAGO
        return ts.tz_localize(tz)
    except Exception:
        return None


def clean_and_qa_dataset(input_path: Path = INPUT_CSV,
                         output_path: Path = OUTPUT_PARQUET) -> pd.DataFrame:
    """Ejecuta el pipeline completo de limpieza, validación y QA/QC sobre el dataset histórico."""
    print(f"Cargando dataset fuente: {input_path}...")
    df = pd.read_csv(input_path, sep=";", encoding="utf-8", low_memory=False)
    n_rows = len(df)
    print(f"Registros leídos: {n_rows:,}")

    # 1. Identificadores y metadatos administrativos
    df_clean = pd.DataFrame()
    df_clean["event_id"] = df["index"].astype(int)
    df_clean["region"] = df["Región"].astype(str).str.strip()
    df_clean["provincia"] = df["Provincia"].astype(str).str.strip()
    df_clean["comuna"] = df["Comuna"].astype(str).str.strip()
    df_clean["codcom"] = df["Codcom"].astype(str).str.strip()
    df_clean["temporada"] = df["temporada"].astype(str).str.strip()

    # 2. Asignación de Splits temporales inmutables
    def assign_split(temp: str) -> str:
        if temp in TRAIN_SEASONS:
            return "train"
        elif temp in VAL_SEASONS:
            return "validation"
        elif temp in TEST_SEASONS:
            return "test"
        return "unknown"

    df_clean["split"] = df_clean["temporada"].apply(assign_split)

    # 3. QA de Coordenadas y corrección de erratas documentadas
    lat_raw = df["Lat Calculada"].apply(parse_float)
    lon_raw = df["Lon Calculada"].apply(parse_float)

    lat_clean = lat_raw.copy()
    lon_clean = lon_raw.copy()
    qa_coord_flag = pd.Series("QA_VALID", index=df.index)

    # Errata 1: Parral index=9386 (336°15'00" S -> -36.25)
    mask_parral = (df["index"] == 9386) & (lat_raw < -300)
    lat_clean.loc[mask_parral] = -36.250000
    qa_coord_flag.loc[mask_parral] = "QA_TYPO_CORRECTED"

    # Errata 2: Ercilla index=25241 (0°03'56" S -> -38.065556)
    mask_ercilla = (df["index"] == 25241) & (lat_raw > -1.0)
    lat_clean.loc[mask_ercilla] = -38.065556
    qa_coord_flag.loc[mask_ercilla] = "QA_TYPO_CORRECTED"

    # Casos sin coordenadas (8 registros)
    mask_null_coord = lat_clean.isna() | lon_clean.isna()
    qa_coord_flag.loc[mask_null_coord] = "QA_MISSING_COORD"

    df_clean["lat"] = lat_clean
    df_clean["lon"] = lon_clean
    df_clean["qa_coord_flag"] = qa_coord_flag

    # 4. Asignación de Celdas H3 (Resolución 8 operacional, Resolución 9 experimental)
    h3_res8 = []
    h3_res9 = []
    for lat_val, lon_val, flag in zip(lat_clean, lon_clean, qa_coord_flag):
        if flag in ("QA_VALID", "QA_TYPO_CORRECTED") and not pd.isna(lat_val) and not pd.isna(lon_val):
            try:
                c8 = h3.latlng_to_cell(lat_val, lon_val, 8)
                c9 = h3.latlng_to_cell(lat_val, lon_val, 9)
                h3_res8.append(c8)
                h3_res9.append(c9)
            except Exception:
                h3_res8.append(None)
                h3_res9.append(None)
        else:
            h3_res8.append(None)
            h3_res9.append(None)

    df_clean["h3_id"] = h3_res8
    df_clean["h3_res9_id"] = h3_res9

    # 5. Tiempos y Zonas Horarias
    # Detectar si el evento es en Isla de Pascua (Rapa Nui lon < -100)
    is_easter = lon_clean < -100.0
    dt_local_list = []
    dt_utc_list = []
    in_br_list = []

    for dt_str, easter_flag in zip(df["Inicio"], is_easter):
        dt_loc = parse_datetime_with_tz(dt_str, is_easter_island=bool(easter_flag))
        if dt_loc is not None:
            dt_utc = dt_loc.tz_convert(TZ_UTC)
            dt_local_list.append(dt_loc)
            dt_utc_list.append(dt_utc)
            in_br_list.append(14 <= dt_loc.hour <= 18)
        else:
            dt_local_list.append(None)
            dt_utc_list.append(None)
            in_br_list.append(False)

    df_clean["datetime_local"] = dt_local_list
    df_clean["datetime_utc"] = dt_utc_list
    df_clean["date_local"] = [dt.date() if dt is not None else None for dt in dt_local_list]
    df_clean["hour_local"] = [dt.hour if dt is not None else None for dt in dt_local_list]
    df_clean["in_br_window"] = in_br_list

    # 6. Superficie y Targets de Severidad (M3)
    final_area = df["Superficie total"].apply(parse_float).fillna(0.0)
    df_clean["final_area_ha"] = final_area
    df_clean["y_ignition"] = 1  # Por definición de evento positivo en el histórico
    df_clean["y_gt10ha"] = (final_area > 10.0).astype(int)
    df_clean["y_gt50ha"] = (final_area > 50.0).astype(int)
    df_clean["y_gt100ha"] = (final_area > 100.0).astype(int)
    df_clean["y_gt1000ha"] = (final_area > 1000.0).astype(int)

    # Desglose de superficies por tipo de combustible
    fuel_area_cols = [
        ("area_arbolado_ha", "Arbolado"),
        ("area_matorral_ha", "Matorral"),
        ("area_pastizal_ha", "Pastizal"),
        ("area_pino_ha", "Pino 0 a 10"),
        ("area_eucalipto_ha", "Eucalipto"),
        ("area_agricola_ha", "Agrícola"),
        ("area_desechos_ha", "Desechos"),
    ]
    for target_col, src_col in fuel_area_cols:
        if src_col in df.columns:
            df_clean[target_col] = df[src_col].apply(parse_float).fillna(0.0)

    # 7. Combustible Inicial y Causas
    df_clean["fuel_initial"] = df["Combustible inicial"].astype(str).str.strip().replace("nan", "Sin dato")
    df_clean["cause_general"] = df["Causa General"].astype(str).str.strip().replace("nan", "Desconocida")
    df_clean["cause_specific"] = df["Causa Específica"].astype(str).str.strip().replace("nan", "Desconocida")

    # 8. QA Cronológico de Hitos Operacionales
    dts_op = {}
    for col_src, col_dst in [
        ("Detección", "dt_deteccion"),
        ("Aviso", "dt_aviso"),
        ("Despacho", "dt_despacho"),
        ("Arribo", "dt_arribo"),
        ("Primer ataque", "dt_primer_ataque"),
        ("Control", "dt_control"),
        ("Extinción", "dt_extincion"),
    ]:
        if col_src in df.columns:
            dts_op[col_dst] = pd.to_datetime(df[col_src], errors="coerce")
            df_clean[col_dst] = dts_op[col_dst]

    dt_ini_raw = pd.to_datetime(df["Inicio"], errors="coerce")
    flag_chrono = (
        (dts_op.get("dt_deteccion", dt_ini_raw) < dt_ini_raw) |
        (dts_op.get("dt_control", dt_ini_raw) < dt_ini_raw) |
        (dts_op.get("dt_extincion", dt_ini_raw) < dts_op.get("dt_control", dt_ini_raw))
    ).fillna(False)

    df_clean["flag_chrono_anomaly"] = flag_chrono

    # 9. Guardar en Parquet optimizado
    print(f"Guardando dataset procesado en {output_path}...")
    df_clean.to_parquet(output_path, index=False)
    print(f"Dataset exportado exitosamente: {len(df_clean):,} registros, {len(df_clean.columns)} columnas.")
    return df_clean


if __name__ == "__main__":
    clean_and_qa_dataset()
