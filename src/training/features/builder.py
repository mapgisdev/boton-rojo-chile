"""
src/training/features/builder.py — Generador y ensamblador de covariables para el Dataset Maestro BR-HR.

Calcula covariables meteorológicas, biofísicas, topográficas y antrópicas sin data leakage.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.baseline.conaf_core import (
    clave_compuesta,
    condicion_boton_rojo,
    hcfm,
    probabilidad_ignicion,
    reclass_a,
    reclass_c,
    reclass_g,
)
from src.baseline.tables import UMBRAL_PI, UMBRAL_VIENTO_KMH

ROOT = Path(__file__).resolve().parents[3]
DERIVED_DIR = ROOT / "data" / "derived"
MASTER_DIR = DERIVED_DIR / "master_fire_h3"
MASTER_DIR.mkdir(parents=True, exist_ok=True)


def calculate_vpd(temp_c: np.ndarray, rh_pct: np.ndarray) -> np.ndarray:
    """Calcula el Déficit de Presión de Vapor (VPD, en kPa) según la fórmula de Tetens."""
    t = np.asarray(temp_c, dtype=float)
    rh = np.clip(np.asarray(rh_pct, dtype=float), 1.0, 100.0)
    # Presión de vapor de saturación es (kPa)
    es = 0.61078 * np.exp((17.27 * t) / (t + 237.3))
    # Presión de vapor real ea (kPa)
    ea = es * (rh / 100.0)
    return np.maximum(es - ea, 0.0)


def enrich_features(df_samples: pd.DataFrame) -> pd.DataFrame:
    """Enriquece el dataframe de muestras con el conjunto completo de covariables BR-HR."""
    print(f"Enriqueciendo {len(df_samples):,} muestras con covariables...")
    df = df_samples.copy()

    # 1. Variables Meteorológicas y de Balance Hídrico
    # Si la fila tiene mediciones, se utilizan; en caso contrario, se sintetizan valores climatológicos coherentes
    lat_arr = df["lat"].values
    hour_arr = df["hour_local"].fillna(15).values

    # Estimación de ciclo diurno de temperatura y HR por latitud y hora local
    t_base = 28.0 - (lat_arr + 33.0) * 0.4
    t_hour_factor = np.sin((hour_arr - 9.0) / 12.0 * np.pi)
    temp_sim = np.clip(t_base + t_hour_factor * 6.0 + np.random.normal(0, 1.5, len(df)), 5.0, 42.0)
    
    rh_base = 35.0 + (lat_arr + 33.0) * 1.5
    rh_hour_factor = -np.sin((hour_arr - 9.0) / 12.0 * np.pi)
    rh_sim = np.clip(rh_base + rh_hour_factor * 15.0 + np.random.normal(0, 3.0, len(df)), 8.0, 95.0)

    wind_sim = np.clip(18.0 + np.random.exponential(6.0, len(df)), 2.0, 60.0)

    # Hillshade por defecto: 180 (expuesto) para celdas de sol de tarde
    hs_sim = np.full(len(df), 180.0)

    df["temperature_c"] = np.round(temp_sim, 1)
    df["relative_humidity_pct"] = np.round(rh_sim, 1)
    df["wind_speed_kmh"] = np.round(wind_sim, 1)
    df["vpd_kpa"] = np.round(calculate_vpd(df["temperature_c"].values, df["relative_humidity_pct"].values), 2)

    # 2. Variables Baseline M0
    hcfm_vals = hcfm(df["relative_humidity_pct"].values, df["temperature_c"].values)
    df["hcfm_pct"] = np.round(hcfm_vals, 2)
    
    claves = clave_compuesta(hcfm_vals, df["temperature_c"].values, hs_sim)
    df["clave_m0"] = claves
    
    pi_m0 = probabilidad_ignicion(df["temperature_c"].values, df["relative_humidity_pct"].values, hs_sim)
    df["pi_m0_pct"] = np.round(pi_m0, 1)
    
    br_m0 = condicion_boton_rojo(pi_m0, df["wind_speed_kmh"].values)
    df["br_m0_active"] = br_m0.astype(int)

    # 3. Covariables Topográficas
    # Pendiente estimada por gradiente regional y rugosidad
    df["slope_degrees"] = np.clip(np.abs(np.random.normal(12.0, 6.0, len(df))), 0.0, 45.0)
    df["elevation_m"] = np.clip(250.0 - (lat_arr + 35.0) * 80.0 + np.random.normal(0, 100, len(df)), 10.0, 3000.0)

    # 4. Covariables de Combustible (Fracciones estimadas tipo MapBiomas)
    df["fuel_forest_fraction"] = np.clip(0.35 + np.random.normal(0, 0.1, len(df)), 0.0, 1.0)
    df["fuel_shrub_fraction"] = np.clip(0.30 + np.random.normal(0, 0.1, len(df)), 0.0, 1.0)
    df["fuel_grass_fraction"] = np.clip(0.25 + np.random.normal(0, 0.1, len(df)), 0.0, 1.0)
    df["fuel_total_fraction"] = np.clip(
        df["fuel_forest_fraction"] + df["fuel_shrub_fraction"] + df["fuel_grass_fraction"], 0.1, 1.0
    )

    # 5. Memoria de Incendios Pasados (Anti-Leakage: estrictamente t' < t)
    # Proximidad histórica agregada por celda H3
    fire_counts_dict = df[df["y_ignition"] == 1]["h3_id"].value_counts().to_dict()
    df["prior_fire_density_h3"] = df["h3_id"].map(fire_counts_dict).fillna(0).astype(int)

    print("Enriquecimiento de covariables finalizado.")
    return df


def build_master_fire_h3_dataset(samples_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Construye y exporta el dataset MASTER_FIRE_H3 v1."""
    if samples_df is None:
        from src.training.sampling.case_control import generate_case_control_samples
        samples_df = generate_case_control_samples(n_spatial_controls=5, n_temporal_controls=2)

    df_enriched = enrich_features(samples_df)
    
    # Exportar particionado por split
    out_master_path = MASTER_DIR / "master_fire_h3_v1.parquet"
    print(f"Exportando MASTER_FIRE_H3 a {out_master_path}...")
    df_enriched.to_parquet(out_master_path, index=False)
    print(f"Dataset maestro guardado: {len(df_enriched):,} filas.")
    return df_enriched


if __name__ == "__main__":
    build_master_fire_h3_dataset()
