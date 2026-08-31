# -*- coding: utf-8 -*-
"""
src/m0_original/daily/accumulation.py — Acumulación diaria del conteo de horas en condición Botón Rojo.
"""

from __future__ import annotations

import numpy as np


def horas_boton_rojo(condiciones_horarias):
    """Calcula el número de horas vespertinas (0..5) en condición de Botón Rojo por píxel.

    Parameters
    ----------
    condiciones_horarias : array-like
        Array booleano con dimensión temporal en el eje 0 (n_horas, ...),
        donde n_horas = 5 correspondientes a 14, 15, 16, 17 y 18 h local.

    Returns
    -------
    np.ndarray (int16)
        Suma de pasos horarios activos por píxel (valores enteros entre 0 y 5).
    """
    arr = np.asarray(condiciones_horarias, dtype=bool)
    return arr.sum(axis=0).astype(np.int16)
