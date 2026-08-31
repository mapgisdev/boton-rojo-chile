# -*- coding: utf-8 -*-
"""
src/m0_original/hourly/activation.py — Evaluación horaria de la condición binaria de Botón Rojo.
"""

from __future__ import annotations

import numpy as np

from src.m0_original.config.constants import UMBRAL_PI, UMBRAL_VIENTO_KMH


def condicion_boton_rojo(pi_pct, viento_kmh_val):
    """Evalúa la regla binaria de activación horaria del Botón Rojo oficial:

        BR_t = (PI_t >= 70 %) AND (Viento_t >= 20 km/h)

    Parameters
    ----------
    pi_pct : float o array-like
        Probabilidad de ignición en %.
    viento_kmh_val : float o array-like
        Velocidad del viento a 10 m en km/h.

    Returns
    -------
    bool o np.ndarray (booleano)
        True donde se cumplen simultáneamente ambas condiciones.
    """
    pi = np.asarray(pi_pct, dtype=float)
    v = np.asarray(viento_kmh_val, dtype=float)
    res = (pi >= UMBRAL_PI) & (v >= UMBRAL_VIENTO_KMH)
    return bool(res) if res.ndim == 0 else res
