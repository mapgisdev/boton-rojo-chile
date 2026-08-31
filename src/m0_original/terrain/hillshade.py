# -*- coding: utf-8 -*-
"""
src/m0_original/terrain/hillshade.py — Cálculo de sombreado topográfico SRTM 90 m (azimut 313°, altitud 60°).
"""

from __future__ import annotations

import numpy as np

from src.m0_original.config.constants import HILLSHADE_ALTITUD, HILLSHADE_AZIMUT


def hillshade(
    dem,
    resolucion_m: float = 90.0,
    azimut: float = HILLSHADE_AZIMUT,
    altitud: float = HILLSHADE_ALTITUD,
):
    """Calcula el sombreado topográfico 0-255 equivalente a la función Hillshade de ArcGIS.

    Parameters
    ----------
    dem : array-like 2D
        Elevaciones en metros.
    resolucion_m : float
        Tamaño de celda en metros (por defecto 90 m para SRTM).
    azimut : float
        Azimut de la fuente luminosa en grados (por defecto 313°).
    altitud : float
        Elevación solar sobre el horizonte en grados (por defecto 60°).

    Returns
    -------
    np.ndarray
        Array 2D de sombreado acotado en [0, 255].
    """
    dem = np.asarray(dem, dtype=float)
    dy, dx = np.gradient(dem, resolucion_m, resolucion_m)
    pendiente = np.arctan(np.hypot(dx, dy))
    aspecto = np.arctan2(-dx, dy)

    # Conversión geométrica a convención de iluminación ArcGIS
    az = np.deg2rad(360.0 - azimut + 90.0)
    zenit = np.deg2rad(90.0 - altitud)

    hs = (
        np.cos(zenit) * np.cos(pendiente)
        + np.sin(zenit) * np.sin(pendiente) * np.cos(az - aspecto)
    )
    return np.clip(255.0 * hs, 0.0, 255.0)
