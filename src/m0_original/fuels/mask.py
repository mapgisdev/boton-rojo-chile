# -*- coding: utf-8 -*-
"""
src/m0_original/fuels/mask.py — Generación y aplicación de la máscara estática de combustible ESA WorldCover 2021.
"""

from __future__ import annotations

import numpy as np

from src.m0_original.config.constants import CLASES_COMBUSTIBLE


def mascara_combustible(worldcover_raster):
    """Genera la máscara booleana estricta de combustible a partir de ESA WorldCover v200.

    Clases consideradas combustible:
    - 10: Árboles / Bosques
    - 20: Matorrales
    - 30: Pastizales
    - 40: Cultivos agrícolas
    - 90: Humedales herbáceos

    Parameters
    ----------
    worldcover_raster : array-like
        Array de códigos enteros de clase de cobertura de suelo.

    Returns
    -------
    np.ndarray (bool)
        True en celdas clasificadas como combustible.
    """
    arr = np.asarray(worldcover_raster)
    return np.isin(np.rint(arr).astype(int), CLASES_COMBUSTIBLE)
