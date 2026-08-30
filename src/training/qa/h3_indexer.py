"""
src/training/qa/h3_indexer.py — Generador del índice territorial H3 resolución 8 y pesos de agregación comunal.

Construye:
1. `data/derived/h3_chile_r8_index.parquet`: Registro maestro de hexágonos H3 Res 8.
2. `data/derived/h3_commune_weights.parquet`: Matriz de pertenencia y ponderación H3 <-> Comuna.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

import h3
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DERIVED_DIR = ROOT / "data" / "derived"
INCENDIOS_PARQUET = DERIVED_DIR / "incendios_qa.parquet"
INDEX_PARQUET = DERIVED_DIR / "h3_chile_r8_index.parquet"
WEIGHTS_PARQUET = DERIVED_DIR / "h3_commune_weights.parquet"


def build_h3_spatial_index(incendios_path: Path = INCENDIOS_PARQUET,
                           index_out_path: Path = INDEX_PARQUET,
                           weights_out_path: Path = WEIGHTS_PARQUET) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Genera la tabla maestra de celdas H3-8 y las ponderaciones comunales a partir del histórico y geometría."""
    print(f"Cargando dataset QA: {incendios_path}...")
    df = pd.read_parquet(incendios_path)
    
    # Filtrar registros con H3 válido
    valid_df = df[df["h3_id"].notna()].copy()
    print(f"Eventos con H3 válido: {len(valid_df):,} sobre {len(df):,}")

    # 1. Agregar estadísticas históricas por celda H3
    print("Agregando estadísticas territoriales por celda H3-8...")
    agg_funcs = {
        "event_id": "count",
        "final_area_ha": "sum",
        "lat": "mean",
        "lon": "mean",
        "codcom": lambda s: s.mode().iat[0] if len(s.mode()) > 0 else s.iat[0],
        "comuna": lambda s: s.mode().iat[0] if len(s.mode()) > 0 else s.iat[0],
        "region": lambda s: s.mode().iat[0] if len(s.mode()) > 0 else s.iat[0],
        "provincia": lambda s: s.mode().iat[0] if len(s.mode()) > 0 else s.iat[0],
    }

    h3_summary = valid_df.groupby("h3_id", as_index=False).agg(agg_funcs)
    h3_summary = h3_summary.rename(columns={
        "event_id": "historical_fire_count",
        "final_area_ha": "historical_burned_ha",
        "lat": "empirical_mean_lat",
        "lon": "empirical_mean_lon",
    })

    # 2. Calcular centroides exactos de H3 según la librería Uber H3
    lat_centers = []
    lon_centers = []
    for cell_id in h3_summary["h3_id"]:
        lat_c, lon_c = h3.cell_to_latlng(cell_id)
        lat_centers.append(lat_c)
        lon_centers.append(lon_c)

    h3_summary["lat_center"] = lat_centers
    h3_summary["lon_center"] = lon_centers
    h3_summary["h3_resolution"] = 8
    h3_summary["cell_area_ha"] = 73.73  # Área teórica promedio de H3 Res 8
    h3_summary["is_fire_history"] = True

    # Guardar índice maestro
    print(f"Exportando índice territorial a {index_out_path}...")
    h3_summary.to_parquet(index_out_path, index=False)
    print(f"Índice H3-8 exportado: {len(h3_summary):,} celdas únicas.")

    # 3. Construir matriz de pesos de intersección H3-Comuna
    # Cada celda H3 se relaciona con su comuna principal con peso base 1.0 (o fraccional en modelos poligonales)
    weights_df = pd.DataFrame({
        "h3_id": h3_summary["h3_id"],
        "codcom": h3_summary["codcom"],
        "comuna": h3_summary["comuna"],
        "provincia": h3_summary["provincia"],
        "region": h3_summary["region"],
        "weight": 1.0,
        "lat_center": h3_summary["lat_center"],
        "lon_center": h3_summary["lon_center"],
        "historical_fire_count": h3_summary["historical_fire_count"],
        "historical_burned_ha": h3_summary["historical_burned_ha"],
    })

    print(f"Exportando tabla de pesos comunales a {weights_out_path}...")
    weights_df.to_parquet(weights_out_path, index=False)
    print(f"Tabla de pesos exportada: {len(weights_df):,} relaciones.")

    return h3_summary, weights_df


if __name__ == "__main__":
    build_h3_spatial_index()
