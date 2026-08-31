# -*- coding: utf-8 -*-
"""
src/m0_original/hcfm/fuel_moisture.py — Regresión lineal de humedad de combustible fino muerto (U. de Chile).
"""

from __future__ import annotations

import numpy as np


def hcfm(hr_pct, temp_c):
    """Calcula la Humedad del Combustible Fino Muerto (HCFM) en % base peso seco.

    Regresión lineal empírica desarrollada por la Universidad de Chile (NASA DEVELOP 2022 Eq. 1):
        HCFM = 0.297374 + 0.262 * HR - 0.00982 * T

    Parameters
    ----------
    hr_pct : float o array-like
        Humedad relativa del aire a 2 m en % (rango 1 a 100).
    temp_c : float o array-like
        Temperatura del aire a 2 m en grados Celsius.

    Returns
    -------
    float o np.ndarray
        HCFM estimada en porcentaje.
    """
    hr_pct = np.asarray(hr_pct, dtype=float)
    temp_c = np.asarray(temp_c, dtype=float)
    return 0.297374 + 0.262 * hr_pct - 0.00982 * temp_c
