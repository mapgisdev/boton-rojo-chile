"""
src/gee/prepare_conaf_asset.py — Preparador de Dataset de Incendios Históricos para Google Earth Engine Asset.

Genera un archivo CSV y GeoJSON optimizado con coordenadas, fecha (YYYY-MM-DD), hora, superficie quemada
y severidad, listo para importar en la pestaña 'Assets' de GEE.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DERIVED_DIR = ROOT / "data" / "derived"
INCENDIOS_PARQUET = DERIVED_DIR / "incendios_qa.parquet"
OUTPUT_CSV = DERIVED_DIR / "incendios_historicos_conaf_asset.csv"
OUTPUT_KEY_EVENTS_JSON = DERIVED_DIR / "fechas_criticas_incendios.json"


def prepare_gee_asset_csv(input_parquet: Path = INCENDIOS_PARQUET,
                          output_csv: Path = OUTPUT_CSV) -> pd.DataFrame:
    """Prepara y exporta el CSV optimizado para subir a Google Earth Engine Assets."""
    print(f"Cargando dataset QA desde {input_parquet}...")
    df = pd.read_parquet(input_parquet)

    # Filtrar eventos con coordenadas válidas
    valid_df = df[df["qa_coord_flag"].isin(["QA_VALID", "QA_TYPO_CORRECTED"])].copy()

    # Seleccionar y renombrar columnas clave para GEE
    asset_df = pd.DataFrame({
        "event_id": valid_df["event_id"],
        "date": valid_df["date_local"].astype(str),
        "hour": valid_df["hour_local"].fillna(15).astype(int),
        "lat": valid_df["lat"].round(5),
        "lon": valid_df["lon"].round(5),
        "area_ha": valid_df["final_area_ha"].round(2),
        "y_gt10ha": valid_df["y_gt10ha"].astype(int),
        "y_gt100ha": valid_df["y_gt100ha"].astype(int),
        "comuna": valid_df["comuna"],
        "region": valid_df["region"],
        "temporada": valid_df["temporada"],
        "split": valid_df["split"],
    })

    print(f"Exportando CSV para GEE Asset a {output_csv}...")
    asset_df.to_csv(output_csv, index=False, encoding="utf-8")
    print(f"CSV generado: {len(asset_df):,} incendios.")

    # Extraer las 10 fechas históricas con mayor cantidad de incendios y superficie quemada
    date_summary = asset_df.groupby("date").agg(
        total_fires=("event_id", "count"),
        total_area_ha=("area_ha", "sum"),
        large_fires_gt100ha=("y_gt100ha", "sum"),
        regions=("region", lambda s: ", ".join(s.unique()[:2])),
    ).reset_index()

    critical_dates = date_summary.sort_values(by="total_area_ha", ascending=False).head(15)
    print("\nTop Fechas Críticas Históricas en Chile:")
    print(critical_dates.to_string(index=False))

    critical_dates_list = critical_dates.to_dict(orient="records")
    with open(OUTPUT_KEY_EVENTS_JSON, "w", encoding="utf-8") as f:
        json.dump(critical_dates_list, f, indent=2)

    return asset_df


if __name__ == "__main__":
    prepare_gee_asset_csv()
