"""
src/training/models/p_ignition.py — Modelo M2: Probabilidad Calibrada de Ignición P(IGN) por H3-8 y hora.

Entrena y compara:
1. Regresión Logística (Baseline interpretable)
2. Random Forest
3. LightGBM (Challenger de alto rendimiento)
Aplica calibración de probabilidades y selecciona el modelo Champion para inferencia.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from src.training.models.calibrator import ProbabilityCalibrator, compute_expected_calibration_error
from src.training.validation.metrics import (
    compute_binary_metrics,
    compute_probabilistic_metrics,
    compute_territorial_concentration,
)

ROOT = Path(__file__).resolve().parents[3]
DERIVED_DIR = ROOT / "data" / "derived"
MASTER_FILE = DERIVED_DIR / "master_fire_h3" / "master_fire_h3_v1.parquet"
ARTIFACTS_M2_DIR = ROOT / "artifacts" / "m2_p_ignition"
ARTIFACTS_M2_DIR.mkdir(parents=True, exist_ok=True)

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


def train_and_evaluate_p_ignition() -> Dict[str, Any]:
    """Entrena los modelos candidatos de P(IGN) y evalúa sobre la partición de validación."""
    print(f"Cargando MASTER_FIRE_H3 desde {MASTER_FILE}...")
    df = pd.read_parquet(MASTER_FILE)

    train_mask = df["split"] == "train"
    val_mask = df["split"] == "validation"

    X_train = df.loc[train_mask, FEATURE_COLS].values
    y_train = df.loc[train_mask, "y_ignition"].values
    weights_train = df.loc[train_mask, "sample_weight"].values

    X_val = df.loc[val_mask, FEATURE_COLS].values
    y_val = df.loc[val_mask, "y_ignition"].values
    weights_val = df.loc[val_mask, "sample_weight"].values

    print(f"Train: {len(X_train):,} muestras | Validation: {len(X_val):,} muestras.")
    print(f"Features ({len(FEATURE_COLS)}): {FEATURE_COLS}")

    # Estandarización para modelos lineales
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)

    results: Dict[str, Any] = {}

    # 1. Regresión Logística (Interpretable)
    print("\n[1/3] Entrenando Regresión Logística...")
    model_lr = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
    model_lr.fit(X_train_scaled, y_train, sample_weight=weights_train)
    y_prob_lr = model_lr.predict_proba(X_val_scaled)[:, 1]

    # Coeficientes interpretables
    lr_coefs = {feat: round(float(c), 4) for feat, c in zip(FEATURE_COLS, model_lr.coef_[0])}
    print("Coeficientes Regresión Logística:", lr_coefs)

    metrics_lr = {
        **compute_probabilistic_metrics(y_val, y_prob_lr, sample_weight=weights_val),
        **compute_territorial_concentration(y_val, y_prob_lr),
        **compute_expected_calibration_error(y_val, y_prob_lr),
    }
    results["logistic_regression"] = metrics_lr
    print("Métricas Logistic:", metrics_lr)

    # 2. Random Forest
    print("\n[2/3] Entrenando Random Forest...")
    model_rf = RandomForestClassifier(
        n_estimators=100, max_depth=12, min_samples_leaf=25, n_jobs=-1, random_state=42
    )
    model_rf.fit(X_train, y_train, sample_weight=weights_train)
    y_prob_rf = model_rf.predict_proba(X_val)[:, 1]

    metrics_rf = {
        **compute_probabilistic_metrics(y_val, y_prob_rf, sample_weight=weights_val),
        **compute_territorial_concentration(y_val, y_prob_rf),
        **compute_expected_calibration_error(y_val, y_prob_rf),
    }
    results["random_forest"] = metrics_rf
    print("Métricas Random Forest:", metrics_rf)

    # 3. LightGBM (Gradient Boosting)
    print("\n[3/3] Entrenando LightGBM (Challenger)...")
    lgb_train = lgb.Dataset(X_train, label=y_train, weight=weights_train, feature_name=FEATURE_COLS)
    lgb_val = lgb.Dataset(X_val, label=y_val, weight=weights_val, reference=lgb_train)

    params = {
        "objective": "binary",
        "metric": "binary_logloss",
        "boosting_type": "gbdt",
        "learning_rate": 0.05,
        "num_leaves": 31,
        "max_depth": 6,
        "min_child_samples": 50,
        "feature_fraction": 0.85,
        "verbose": -1,
        "seed": 42,
    }

    model_lgb = lgb.train(
        params,
        lgb_train,
        num_boost_round=200,
        valid_sets=[lgb_val],
        callbacks=[lgb.early_stopping(stopping_rounds=20, verbose=False)],
    )

    y_prob_lgb = model_lgb.predict(X_val)

    metrics_lgb = {
        **compute_probabilistic_metrics(y_val, y_prob_lgb, sample_weight=weights_val),
        **compute_territorial_concentration(y_val, y_prob_lgb),
        **compute_expected_calibration_error(y_val, y_prob_lgb),
    }
    results["lightgbm_raw"] = metrics_lgb
    print("Métricas LightGBM Raw:", metrics_lgb)

    # 4. Calibración de Probabilidades del Champion (LightGBM)
    print("\nCalibrando probabilidades de LightGBM (Isotonic Calibration)...")
    calibrator = ProbabilityCalibrator(method="isotonic")
    calibrator.fit(y_prob_lgb, y_val)
    y_prob_calibrated = calibrator.predict_proba(y_prob_lgb)

    metrics_champion_cal = {
        **compute_probabilistic_metrics(y_val, y_prob_calibrated, sample_weight=weights_val),
        **compute_territorial_concentration(y_val, y_prob_calibrated),
        **compute_expected_calibration_error(y_val, y_prob_calibrated),
    }
    results["champion_lightgbm_calibrated"] = metrics_champion_cal
    print("Métricas Champion Calibrado:", metrics_champion_cal)

    # Importancia de variables
    importance = dict(zip(FEATURE_COLS, [int(x) for x in model_lgb.feature_importance(importance_type="gain")]))
    importance_sorted = dict(sorted(importance.items(), key=lambda item: item[1], reverse=True))

    # 5. Guardar artefactos
    model_lgb_file = ARTIFACTS_M2_DIR / "champion_lightgbm.txt"
    model_lgb.save_model(str(model_lgb_file))

    lr_file = ARTIFACTS_M2_DIR / "logistic_regression_coefficients.json"
    with open(lr_file, "w", encoding="utf-8") as f:
        json.dump({"coefficients": lr_coefs, "intercept": float(model_lr.intercept_[0])}, f, indent=2)

    model_card = {
        "model_id": "M2_P_IGNITION_CHAMPION_v1.0",
        "model_type": "LightGBM + Isotonic Calibration",
        "target": "P(ignition | h3, hour)",
        "train_samples": len(X_train),
        "validation_samples": len(X_val),
        "feature_importance_gain": importance_sorted,
        "metrics_validation": metrics_champion_cal,
        "benchmark_comparison": results,
    }

    card_file = ARTIFACTS_M2_DIR / "model_card_m2.json"
    with open(card_file, "w", encoding="utf-8") as f:
        json.dump(model_card, f, indent=2)

    print(f"Artefactos M2 guardados en {ARTIFACTS_M2_DIR}")
    return results


if __name__ == "__main__":
    train_and_evaluate_p_ignition()
