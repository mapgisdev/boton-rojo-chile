# -*- coding: utf-8 -*-
"""
src/m0_original/validation/conaf_fidelity.py — Métricas de fidelidad y evaluación comparativa M0 vs CONAF publicado.
"""

from __future__ import annotations

from typing import Dict
import numpy as np
import pandas as pd


def calcular_metricas_fidelidad(
    df_m0: pd.DataFrame,
    df_conaf: pd.DataFrame,
    tolerancia_ha: float = 25.0,
) -> Dict[str, float]:
    """Calcula las métricas de fidelidad cuantitativas entre la réplica M0 y el producto oficial CONAF.

    Parameters
    ----------
    df_m0 : pd.DataFrame
        Salida comunal de M0 (columnas: date, com_id, horas, SUM_br_ha, com_ha, proportion).
    df_conaf : pd.DataFrame
        Salida comunal cosechada de CONAF (mismas columnas).
    tolerancia_ha : float
        Tolerancia en hectáreas para considerar una coincidencia de com_ha (por defecto 25 ha).

    Returns
    -------
    Dict[str, float]
        Métricas calculadas: MAE com_ha, MAE SUM_br_ha, MAE proportion, correlación, F1 comunal.
    """
    if df_m0.empty or df_conaf.empty:
        return {
            "mae_com_ha": np.nan,
            "mae_sum_br_ha": np.nan,
            "mae_proportion": np.nan,
            "correlacion_proportion": np.nan,
            "f1_comunal": 0.0,
            "coincidencia_exacta_pct": 0.0,
        }

    # 1. Cruzar por fecha, com_id y horas
    cruce = pd.merge(
        df_m0,
        df_conaf,
        on=["date", "com_id", "horas"],
        suffixes=("_m0", "_conaf"),
        how="outer",
    )

    # Identificar verdaderos positivos, falsos positivos y falsos negativos comunales
    ambos = cruce.dropna(subset=["SUM_br_ha_m0", "SUM_br_ha_conaf"])
    tp = len(ambos)
    fp = cruce["SUM_br_ha_conaf"].isna().sum()
    fn = cruce["SUM_br_ha_m0"].isna().sum()

    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) > 0 else 0.0

    if ambos.empty:
        return {
            "mae_com_ha": np.nan,
            "mae_sum_br_ha": np.nan,
            "mae_proportion": np.nan,
            "correlacion_proportion": np.nan,
            "f1_comunal": round(f1, 4),
            "coincidencia_exacta_pct": 0.0,
        }

    mae_com_ha = float(
        np.abs(ambos["com_ha_m0"] - ambos["com_ha_conaf"]).mean()
    )
    mae_sum_ha = float(
        np.abs(ambos["SUM_br_ha_m0"] - ambos["SUM_br_ha_conaf"]).mean()
    )
    mae_prop = float(
        np.abs(ambos["proportion_m0"] - ambos["proportion_conaf"]).mean()
    )

    corr = float(
        ambos["proportion_m0"].corr(ambos["proportion_conaf"])
        if len(ambos) > 1
        else 1.0
    )

    exactas = np.isclose(
        ambos["SUM_br_ha_m0"], ambos["SUM_br_ha_conaf"], atol=tolerancia_ha
    ).mean()

    return {
        "mae_com_ha": round(mae_com_ha, 2),
        "mae_sum_br_ha": round(mae_sum_ha, 2),
        "mae_proportion": round(mae_prop, 4),
        "correlacion_proportion": round(corr, 4),
        "f1_comunal": round(f1, 4),
        "coincidencia_exacta_pct": round(float(exactas) * 100.0, 2),
    }
