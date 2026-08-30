"""
src/training/sampling/case_control.py — Muestreo Caso-Control Espacio-Temporal para BR-HR.

Genera pares contrastantes de ignición (positivos y controles) dentro del universo territorial H3-8:
1. Positivos (y=1): Eventos históricos georreferenciados.
2. Controles espaciales (y=0): Mismo día y hora, misma región/comuna, celdas H3 combustibles sin ignición.
3. Controles temporales (y=0): Misma celda H3, hora y época comparable, fechas sin ignición.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.shared.time_utils import TZ_EASTER, TZ_SANTIAGO, TZ_UTC

ROOT = Path(__file__).resolve().parents[3]
DERIVED_DIR = ROOT / "data" / "derived"
INCENDIOS_PARQUET = DERIVED_DIR / "incendios_qa.parquet"
INDEX_PARQUET = DERIVED_DIR / "h3_chile_r8_index.parquet"
OUTPUT_DIR = DERIVED_DIR / "master_fire_h3"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_case_control_samples(incendios_path: Path = INCENDIOS_PARQUET,
                                  index_path: Path = INDEX_PARQUET,
                                  n_spatial_controls: int = 5,
                                  n_temporal_controls: int = 2,
                                  max_positives: Optional[int] = None,
                                  seed: int = 42) -> pd.DataFrame:
    """Genera el dataset caso-control completo con pesos de muestreo reproducibles."""
    print(f"Cargando dataset QA desde {incendios_path}...")
    df_pos = pd.read_parquet(incendios_path)
    # Filtrar únicamente eventos con celda H3 válida
    df_pos = df_pos[df_pos["h3_id"].notna()].copy()
    if max_positives is not None and max_positives < len(df_pos):
        df_pos = df_pos.sample(n=max_positives, random_state=seed).reset_index(drop=True)

    n_pos = len(df_pos)
    print(f"Positivos válidos para muestreo: {n_pos:,}")

    print(f"Cargando universo de celdas H3 desde {index_path}...")
    df_h3 = pd.read_parquet(index_path)
    all_h3_cells = df_h3["h3_id"].values
    h3_by_region: Dict[str, List[str]] = df_h3.groupby("region")["h3_id"].apply(list).to_dict()
    h3_metadata = df_h3.set_index("h3_id")[["codcom", "comuna", "region", "provincia", "lat_center", "lon_center"]].to_dict(orient="index")

    fire_set = set(zip(df_pos["h3_id"], df_pos["date_local"]))
    all_dates = list(df_pos["date_local"].dropna().unique())

    rng = np.random.default_rng(seed)
    random.seed(seed)

    rows: List[Dict] = []

    # 1. Procesar Positivos
    print("Registrando eventos positivos...")
    for row in df_pos.itertuples(index=False):
        rows.append({
            "sample_id": f"pos_{row.event_id}",
            "event_id": row.event_id,
            "h3_id": row.h3_id,
            "codcom": row.codcom,
            "comuna": row.comuna,
            "region": row.region,
            "provincia": row.provincia,
            "lat": row.lat,
            "lon": row.lon,
            "datetime_local": row.datetime_local,
            "datetime_utc": row.datetime_utc,
            "date_local": row.date_local,
            "hour_local": row.hour_local,
            "temporada": row.temporada,
            "split": row.split,
            "in_br_window": row.in_br_window,
            "sample_type": "positive",
            "y_ignition": 1,
            "sample_weight": 1.0,
            "inclusion_probability": 1.0,
            "final_area_ha": row.final_area_ha,
            "y_gt10ha": row.y_gt10ha,
            "y_gt50ha": row.y_gt50ha,
            "y_gt100ha": row.y_gt100ha,
            "y_gt1000ha": row.y_gt1000ha,
            "fuel_initial": row.fuel_initial,
            "cause_general": row.cause_general,
        })

    # 2. Generar Controles Espaciales
    print(f"Generando {n_spatial_controls} controles espaciales por positivo...")
    for row in df_pos.itertuples(index=False):
        region_cells = h3_by_region.get(row.region, all_h3_cells)
        sample_k = min(len(region_cells), max(n_spatial_controls * 3, 10))
        candidate_cells = [c for c in random.sample(region_cells, sample_k) if c != row.h3_id]
        
        selected_sp = 0
        for cand_cell in candidate_cells:
            if (cand_cell, row.date_local) not in fire_set:
                meta = h3_metadata[cand_cell]
                rows.append({
                    "sample_id": f"sp_{row.event_id}_{selected_sp}",
                    "event_id": None,
                    "h3_id": cand_cell,
                    "codcom": meta["codcom"],
                    "comuna": meta["comuna"],
                    "region": meta["region"],
                    "provincia": meta["provincia"],
                    "lat": meta["lat_center"],
                    "lon": meta["lon_center"],
                    "datetime_local": row.datetime_local,
                    "datetime_utc": row.datetime_utc,
                    "date_local": row.date_local,
                    "hour_local": row.hour_local,
                    "temporada": row.temporada,
                    "split": row.split,
                    "in_br_window": row.in_br_window,
                    "sample_type": "spatial_control",
                    "y_ignition": 0,
                    "sample_weight": 1.0 / n_spatial_controls,
                    "inclusion_probability": 1.0 / len(region_cells),
                    "final_area_ha": 0.0,
                    "y_gt10ha": 0,
                    "y_gt50ha": 0,
                    "y_gt100ha": 0,
                    "y_gt1000ha": 0,
                    "fuel_initial": "Sin ignición",
                    "cause_general": "Control",
                })
                selected_sp += 1
                if selected_sp >= n_spatial_controls:
                    break

    # 3. Generar Controles Temporales
    print(f"Generando {n_temporal_controls} controles temporales por positivo...")
    for row in df_pos.itertuples(index=False):
        sample_k = min(len(all_dates), max(n_temporal_controls * 4, 10))
        rand_dates = random.sample(all_dates, sample_k)
        selected_tp = 0
        for cand_date in rand_dates:
            if (row.h3_id, cand_date) not in fire_set:
                tz_target = TZ_EASTER if row.lon < -100.0 else TZ_SANTIAGO
                try:
                    dt_cand_local = pd.Timestamp(
                        year=cand_date.year,
                        month=cand_date.month,
                        day=cand_date.day,
                        hour=int(row.hour_local) if row.hour_local is not None else 15,
                        tz=tz_target
                    )
                    dt_cand_utc = dt_cand_local.tz_convert(TZ_UTC)
                except Exception:
                    continue

                rows.append({
                    "sample_id": f"tp_{row.event_id}_{selected_tp}",
                    "event_id": None,
                    "h3_id": row.h3_id,
                    "codcom": row.codcom,
                    "comuna": row.comuna,
                    "region": row.region,
                    "provincia": row.provincia,
                    "lat": row.lat,
                    "lon": row.lon,
                    "datetime_local": dt_cand_local,
                    "datetime_utc": dt_cand_utc,
                    "date_local": cand_date,
                    "hour_local": row.hour_local,
                    "temporada": row.temporada,
                    "split": row.split,
                    "in_br_window": row.in_br_window,
                    "sample_type": "temporal_control",
                    "y_ignition": 0,
                    "sample_weight": 1.0 / n_temporal_controls,
                    "inclusion_probability": 1.0 / len(all_dates),
                    "final_area_ha": 0.0,
                    "y_gt10ha": 0,
                    "y_gt50ha": 0,
                    "y_gt100ha": 0,
                    "y_gt1000ha": 0,
                    "fuel_initial": "Sin ignición",
                    "cause_general": "Control",
                })
                selected_tp += 1
                if selected_tp >= n_temporal_controls:
                    break

    df_master = pd.DataFrame(rows)
    print(f"Dataset caso-control generado: {len(df_master):,} filas totales.")
    return df_master


if __name__ == "__main__":
    df_samples = generate_case_control_samples()
    out_file = OUTPUT_DIR / "case_control_samples.parquet"
    print(f"Guardando en {out_file}...")
    df_samples.to_parquet(out_file, index=False)
    print("Completado.")
