# -*- coding: utf-8 -*-
"""
src/m0_original/meteorology/wind.py — Cálculo del módulo escalar de viento a 10 m en km/h.
"""

from __future__ import annotations

import numpy as np


def viento_kmh(u10, v10):
    """Calcula la velocidad del viento a 10 m en km/h a partir de componentes u y v en m/s.

    Fórmula oficial:
        V = sqrt(u^2 + v^2) * 3.6

    Parameters
    ----------
    u10 : float o array-like
        Componente zonal del viento a 10 m en m/s.
    v10 : float o array-like
        Componente meridional del viento a 10 m en m/s.

    Returns
    -------
    float o np.ndarray
        Velocidad escalar del viento en km/h.
    """
    u10 = np.asarray(u10, dtype=float)
    v10 = np.asarray(v10, dtype=float)
    return np.hypot(u10, v10) * 3.6
