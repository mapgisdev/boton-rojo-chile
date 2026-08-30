"""
src/training/models/p_large_fire.py — Modelo M3: Potencial Condicional de Grandes Incendios P(GF).

Calcula la probabilidad condicional de que una ignición confirmada supere umbrales críticos de superficie:
- Target 1: P(A > 10 ha | ignición)
- Target 2: P(A > 100 ha | ignición)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import lightgbm as lgb
import numpy as np
import pandas as pd

from src.training.models.calibrator import compute_expected_calibration_error
from src.training.validation.metrics import (
    compute_binary_metrics,
    compute_probabilistic_metrics,
    compute_territorial_concentration,
)

ROOT = Path(__file__).resolve().parents[3]
DERIVED_DIR = ROOT / "data" / "derived"
MASTER_FILE = DERIVED_DIR / "master_fire_h3" / "master_fire_h3_v1.parquet"
ARTIFACTS_M3_DIR = ROOT / "artifacts" / "m3_p_large_fire"
ARTIFACTS_M3_DIR.mkdir(parents=True, exist_ok=True)

FEATURE_COLS = [
    "temperature_c",
    "relative_humidity_pct",
    "wind_speed_kmh",
    "vpd_kpa",
    "hcfm_pct",
    "pi_m0_pct",
    "slope_degrees",
    "elevation_m",
    "fuel_forest_fraction",
    "fuel_shrub_fraction",
    "fuel_grass_fraction",
    "fuel_total_fraction",
    "prior_fire_density_h3",
]


def train_conditional_large_fire_model(target_col: str = "y_gt10ha") -> Dict[str, Any]:
    """Entrena y valida un modelo condicional de gran incendio sobre las igniciones confirmadas."""
    print(f"\n--- Entrenando modelo M3 para {target_col} ---")
    df = pd.read_parquet(MASTER_FILE)

    # Filtrar estrictamente sobre igniciones positivas
    df_pos = df[df["y_ignition"] == 1].copy()

    train_mask = df_pos["split"] == "train"
    val_mask = df_pos["split"] == "validation"

    X_train = df_pos.loc[train_mask, FEATURE_COLS].values
    y_train = df_pos.loc[train_mask, target_col].values

    X_val = df_pos.loc[val_mask, FEATURE_COLS].values
    y_val = df_pos.loc[val_mask, target_col].values

    print(f"Igniciones Train: {len(X_train):,} ({y_train.sum():,} positivos {target_col}, {y_train.mean()*100:.2f} %)")
    print(f"Igniciones Val:   {len(X_val):,} ({y_val.sum():,} positivos {target_col}, {y_val.mean()*100:.2f} %)")

    lgb_train = lgb.Dataset(X_train, label=y_train, feature_name=FEATURE_COLS)
    lgb_val = lgb.Dataset(X_val, label=y_val, reference=lgb_train)

    params = {
        "objective": "binary",
        "metric": "binary_logloss",
        "boosting_type": "gbdt",
        "learning_rate": 0.03,
        "num_leaves": 20,
        "max_depth": 5,
        "min_child_samples": 40,
        "feature_fraction": 0.85,
        "verbose": -1,
        "seed": 42,
    }

    model = lgb.train(
        params,
        lgb_train,
        num_boost_round=150,
        valid_sets=[lgb_val],
        callbacks=[lgb.early_stopping(stopping_rounds=15, verbose=False)],
    )

    y_prob = model.predict(X_val)

    metrics = {
        "target": target_col,
        "train_samples": int(len(X_train)),
        "validation_samples": int(len(X_val)),
        **compute_probabilistic_metrics(y_val, y_prob),
        **compute_expected_calibration_error(y_val, y_prob),
        **compute_territorial_concentration(y_val, y_prob),
    }

    print(f"Métricas M3 ({target_col}): PR-AUC={metrics['pr_auc']:.4f}, ROC-AUC={metrics['roc_auc']:.4f}, Brier={metrics['brier_score']:.6f}, ECE={metrics['ece']:.4f}")

    # Guardar modelo
    model_file = ARTIFACTS_M3_DIR / f"model_m3_{target_col}.txt"
    model.save_model(str(model_file))

    return metrics


def run_phase_5_large_fire_models() -> Dict[str, Any]:
    """Entrena ambos targets de gran incendio (10 ha y 100 ha) y guarda model card."""
    metrics_10ha = train_conditional_large_fire_model("y_gt10ha")
    metrics_100ha = train_conditional_large_fire_model("y_gt100ha")

    summary = {
        "model_id": "M3_P_LARGE_FIRE_v1.0",
        "description": "Modelos condicionales de potencial de gran incendio P(A > umbral | ignicion)",
        "models": {
            "p_gt10ha": metrics_10ha,
            "p_gt100ha": metrics_100ha,
        }
    }

    card_path = ARTIFACTS_M3_DIR / "model_card_m3.json"
    with open(card_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Model Card M3 guardada en {card_path}")
    return summary


if __name__ == "__main__":
    run_phase_5_large_fire_models()
