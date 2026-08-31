# -*- coding: utf-8 -*-
"""
src/m0_original/reclass/tables.py — Las siete tablas de reclasificación oficiales (Reclass A a G).
"""

from __future__ import annotations

import numpy as np

from src.m0_original.config.constants import (
    CODIGO_EXPUESTO,
    CODIGO_SOMBREADO,
    RECLASS_G_CORTE,
)

# ---------------------------------------------------------------------------
# Definiciones de Cortes y Etiquetas Oficiales
# ---------------------------------------------------------------------------

# Reclass A — Temperatura (°C) -> clases 1..9
RECLASS_A_CORTES = [0, 5, 10, 15, 20, 25, 30, 35, 40]
RECLASS_A_ETIQUETAS = [
    "Menor a 0",
    "0 - 5",
    "5 - 10",
    "10 - 15",
    "15 - 20",
    "20 - 25",
    "25 - 30",
    "30 - 35",
    "Mayor a 35",
]
RECLASS_A_REPRESENTANTE = [-2.5, 2.5, 7.5, 12.5, 17.5, 22.5, 27.5, 32.5, 37.5]

# Reclass B — HCFM (%) -> clases 1..10 (Simbología capa HC)
RECLASS_B_CORTES = [2, 4, 6, 8, 10, 12, 15, 20, 25]
RECLASS_B_ETIQUETAS = [
    "0 - 2",
    "2 - 4",
    "4 - 6",
    "6 - 8",
    "8 - 10",
    "10 - 12",
    "12 - 15",
    "15 - 20",
    "20 - 25",
    "Mayor a 25",
]

# Reclass C — HCFM (%) -> millares 2000..17000 (Indexación Matriz PI)
RECLASS_C_CORTES = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 30]
RECLASS_C_VALORES = [
    2000,
    3000,
    4000,
    5000,
    6000,
    7000,
    8000,
    9000,
    10000,
    11000,
    12000,
    13000,
    14000,
    15000,
    16000,
    17000,
]

# Reclass D — PI (%) -> deciles 1..10 (Simbología capa PI)
RECLASS_D_CORTES = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

# Reclass E — Viento (km/h) -> clases 1..8 (Simbología capa VV)
RECLASS_E_CORTES = [3, 5, 10, 15, 20, 25, 30]
RECLASS_E_ETIQUETAS = [
    "Calmo",
    "3 - 5",
    "5 - 10",
    "10 - 15",
    "15 - 20",
    "20 - 25",
    "25 - 30",
    "Mayor a 30",
]


def reclass_a(temp_c):
    """Reclass A: Temperatura (°C) -> clase entera 1..9.

    Valores > 40 °C producen 0 (NoData / Fuera de Dominio).
    """
    t = np.asarray(temp_c, dtype=float)
    clase = np.zeros(t.shape, dtype=np.int16)
    inferior = -np.inf
    for i, superior in enumerate(RECLASS_A_CORTES, start=1):
        clase = np.where((t > inferior) & (t <= superior), i, clase)
        inferior = superior
    return clase if clase.ndim > 0 else int(clase)


def reclass_b(hcfm_pct):
    """Reclass B: HCFM (%) -> clase visual 1..10."""
    m = np.asarray(hcfm_pct, dtype=float)
    clase = np.zeros(m.shape, dtype=np.int16)
    inferior = -np.inf
    for i, superior in enumerate(RECLASS_B_CORTES, start=1):
        clase = np.where((m > inferior) & (m <= superior), i, clase)
        inferior = superior
    clase = np.where(m > RECLASS_B_CORTES[-1], 10, clase)
    return clase if clase.ndim > 0 else int(clase)


def reclass_c(hcfm_pct):
    """Reclass C: HCFM (%) -> clave de millares 2000..17000.

    Valores > 30 % producen 0 (NoData / Fuera de Dominio).
    """
    m = np.asarray(hcfm_pct, dtype=float)
    clave = np.zeros(m.shape, dtype=np.int32)
    inferior = 0.0
    for superior, valor in zip(RECLASS_C_CORTES, RECLASS_C_VALORES):
        clave = np.where((m > inferior) & (m <= superior), valor, clave)
        inferior = superior
    return clave if clave.ndim > 0 else int(clave)


def reclass_d(pi_pct):
    """Reclass D: PI (%) -> decil visual 1..10 (o etiqueta 10..100)."""
    p = np.asarray(pi_pct, dtype=float)
    decil = np.clip(np.ceil(p / 10.0), 1, 10).astype(np.int16)
    return decil if decil.ndim > 0 else int(decil)


def reclass_e(viento):
    """Reclass E: Viento (km/h) -> clase visual 1..8."""
    v = np.asarray(viento, dtype=float)
    clase = np.zeros(v.shape, dtype=np.int16)
    inferior = -np.inf
    for i, superior in enumerate(RECLASS_E_CORTES, start=1):
        clase = np.where((v > inferior) & (v <= superior), i, clase)
        inferior = superior
    clase = np.where(v > RECLASS_E_CORTES[-1], 8, clase)
    return clase if clase.ndim > 0 else int(clase)


def reclass_f(viento):
    """Reclass F: Viento (km/h) -> binario (0 si < 20 km/h, 1 si >= 20 km/h)."""
    v = np.asarray(viento, dtype=float)
    binario = np.where(v >= 20.0, 1, 0).astype(np.int16)
    return binario if binario.ndim > 0 else int(binario)


def reclass_g(hs):
    """Reclass G: Hillshade 0-255 -> 200 (Sombreado <= 123.5) o 100 (Expuesto > 123.5)."""
    hs = np.asarray(hs, dtype=float)
    res = np.where(hs <= RECLASS_G_CORTE, CODIGO_SOMBREADO, CODIGO_EXPUESTO).astype(np.int16)
    return res if res.ndim > 0 else int(res)
