# -*- coding: utf-8 -*-
"""
src/m0_original/ignition_matrix/matrix_loader.py — Indexación y consulta de claves compuestas en la matriz PI.
"""

from __future__ import annotations

from typing import Dict, Optional
import numpy as np

from src.m0_original.hcfm.fuel_moisture import hcfm
from src.m0_original.ignition_matrix.rothermel_engine import construir_matriz_pi
from src.m0_original.reclass.tables import reclass_a, reclass_c, reclass_g

# Instancia congelada por defecto (Rothermel / BehavePlus)
MATRIZ_PI_ROTHERMEL: Dict[int, float] = construir_matriz_pi()


def clave_pi(hcfm_pct, temp_c, hs):
    """Calcula la clave compuesta entera: ReclassC + ReclassG + ReclassA.

    Valores fuera de dominio (T > 40 °C o HCFM > 30 %) producen clave 0 (NoData).

    Parameters
    ----------
    hcfm_pct : float o array-like
        Humedad del combustible fino muerto en %.
    temp_c : float o array-like
        Temperatura del aire en °C.
    hs : float o array-like
        Hillshade topográfico (0-255).

    Returns
    -------
    int o np.ndarray
        Clave compuesta (2101..17209) o 0 si está fuera de dominio.
    """
    c = np.asarray(reclass_c(hcfm_pct), dtype=np.int32)
    g = np.asarray(reclass_g(hs), dtype=np.int32)
    a = np.asarray(reclass_a(temp_c), dtype=np.int32)

    clave = c + g + a
    invalido = (c == 0) | (a == 0)
    res = np.where(invalido, 0, clave)
    return res if res.ndim > 0 else int(res)


def probabilidad_ignicion(
    temp_c,
    hr_pct,
    hs,
    matriz: Optional[Dict[int, float]] = None,
):
    """Calcula la Probabilidad de Ignición (%) por la vía oficial CONAF: HCFM -> Clave -> Matriz.

    Devuelve NaN donde la clave cae fuera del dominio de las tablas.

    Parameters
    ----------
    temp_c : float o array-like
        Temperatura del aire en °C.
    hr_pct : float o array-like
        Humedad relativa en %.
    hs : float o array-like
        Hillshade (0-255).
    matriz : Dict[int, float], opcional
        Matriz de 288 celdas (por defecto MATRIZ_PI_ROTHERMEL).

    Returns
    -------
    float o np.ndarray
        Probabilidad de ignición porcentual (0 a 100 %).
    """
    mat = MATRIZ_PI_ROTHERMEL if matriz is None else matriz
    t = np.asarray(temp_c, dtype=float)
    hr = np.asarray(hr_pct, dtype=float)
    hs_arr = np.asarray(hs, dtype=float)

    m = hcfm(hr, t)
    claves = np.asarray(clave_pi(m, t, hs_arr), dtype=np.int32)

    max_clave = max(mat.keys()) if mat else 17209
    lookup = np.full(max_clave + 1, np.nan, dtype=float)
    for k, v in mat.items():
        if k <= max_clave:
            lookup[k] = v

    es_escalar = claves.ndim == 0
    c_flat = np.atleast_1d(claves)
    pi_flat = np.where(
        (c_flat > 0) & (c_flat <= max_clave),
        lookup[np.clip(c_flat, 0, max_clave)],
        np.nan,
    )

    return float(pi_flat[0]) if es_escalar else pi_flat.reshape(claves.shape)
