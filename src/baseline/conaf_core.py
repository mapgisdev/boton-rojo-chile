"""
src/baseline/conaf_core.py — Implementación pura y desacoplada del algoritmo Botón Rojo de CONAF (M0).

Diseño:
- 100 % Python puro con NumPy, sin I/O ni dependencias pesadas.
- Soporta tanto entradas escalares como arrays n-dimensionales (grids espaciales o series temporales).
- Incluye correcciones de robustez técnica en los bordes de dominio sin alterar la lógica científica.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple, Union
import numpy as np

from src.baseline.pi_matrix import MATRIZ_BASE_ROTHERMEL
from src.baseline.tables import (
    CODIGO_EXPUESTO,
    CODIGO_SOMBREADO,
    HILLSHADE_ALTITUD,
    HILLSHADE_AZIMUT,
    RECLASS_A_CORTES,
    RECLASS_B_CORTES,
    RECLASS_C_CORTES,
    RECLASS_C_VALORES,
    RECLASS_E_CORTES,
    RECLASS_G_CORTE,
    UMBRAL_PI,
    UMBRAL_VIENTO_KMH,
)

ArrayOrFloat = Union[float, np.ndarray]


def hcfm(hr_pct: ArrayOrFloat, temp_c: ArrayOrFloat) -> ArrayOrFloat:
    """Calcula la Humedad del Combustible Fino Muerto (HCFM, en %) según la regresión U. de Chile.

        HCFM = 0.297374 + 0.262 * HR - 0.00982 * T

    Parameters
    ----------
    hr_pct : Humedad relativa a 2m, en % (1.0 a 100.0).
    temp_c : Temperatura a 2m, en °C.
    """
    hr_arr = np.asarray(hr_pct, dtype=float)
    t_arr = np.asarray(temp_c, dtype=float)
    res = 0.297374 + 0.262 * hr_arr - 0.00982 * t_arr
    if np.isscalar(hr_pct) and np.isscalar(temp_c):
        return float(res)
    return res


def viento_kmh(u10: ArrayOrFloat, v10: ArrayOrFloat) -> ArrayOrFloat:
    """Calcula la velocidad del viento a 10m en km/h a partir de componentes u y v en m/s.

        V = sqrt(u^2 + v^2) * 3.6
    """
    u_arr = np.asarray(u10, dtype=float)
    v_arr = np.asarray(v10, dtype=float)
    res = np.hypot(u_arr, v_arr) * 3.6
    if np.isscalar(u10) and np.isscalar(v10):
        return float(res)
    return res


def hillshade(dem: np.ndarray,
              resolucion_m: float,
              azimut: float = HILLSHADE_AZIMUT,
              altitud: float = HILLSHADE_ALTITUD) -> np.ndarray:
    """Calcula el sombreado topográfico (0..255) equivalente a ArcGIS Hillshade y GEE ee.Terrain.hillshade.

    Parameters
    ----------
    dem : Array 2D con elevaciones en metros.
    resolucion_m : Tamaño de celda en metros.
    azimut : Ángulo del sol respecto al norte (313.0° en CONAF).
    altitud : Elevación solar sobre el horizonte (60.0° en CONAF).
    """
    dem_arr = np.asarray(dem, dtype=float)
    dy, dx = np.gradient(dem_arr, resolucion_m, resolucion_m)
    pendiente = np.arctan(np.hypot(dx, dy))
    aspecto = np.arctan2(-dx, dy)

    az_rad = np.deg2rad(360.0 - azimut + 90.0)
    zenit_rad = np.deg2rad(90.0 - altitud)

    hs = np.cos(zenit_rad) * np.cos(pendiente) + np.sin(zenit_rad) * np.sin(pendiente) * np.cos(az_rad - aspecto)
    return np.clip(255.0 * hs, 0.0, 255.0)


def reclass_a(temp_c: ArrayOrFloat, modo_seguro: bool = True) -> np.ndarray | int:
    """Reclass A: Temperatura (°C) -> clase 1..9.

    Si modo_seguro es True, temperaturas > 40 °C se asignan a la clase 9 (en vez de quedar como NoData/0).
    """
    t_arr = np.asarray(temp_c, dtype=float)
    clase = np.zeros(t_arr.shape, dtype=np.int16)
    inferior = -np.inf

    for i, superior in enumerate(RECLASS_A_CORTES, start=1):
        clase = np.where((t_arr > inferior) & (t_arr <= superior), i, clase)
        inferior = superior

    if modo_seguro:
        clase = np.where(t_arr > RECLASS_A_CORTES[-1], len(RECLASS_A_CORTES), clase)
        clase = np.where(t_arr < RECLASS_A_CORTES[0], 1, clase)

    if np.isscalar(temp_c):
        return int(clase.item())
    return clase


def reclass_c(hcfm_pct: ArrayOrFloat, modo_seguro: bool = True) -> np.ndarray | int:
    """Reclass C: HCFM (%) -> clave de millares 2000..17000.

    Si modo_seguro es True, humedades > 30 % se asignan a 17000 y <= 0 % a 2000.
    """
    m_arr = np.asarray(hcfm_pct, dtype=float)
    clave = np.zeros(m_arr.shape, dtype=np.int32)
    inferior = 0.0

    for superior, valor in zip(RECLASS_C_CORTES, RECLASS_C_VALORES):
        clave = np.where((m_arr > inferior) & (m_arr <= superior), valor, clave)
        inferior = superior

    if modo_seguro:
        clave = np.where(m_arr > RECLASS_C_CORTES[-1], RECLASS_C_VALORES[-1], clave)
        clave = np.where(m_arr <= 0.0, RECLASS_C_VALORES[0], clave)

    if np.isscalar(hcfm_pct):
        return int(clave.item())
    return clave


def reclass_g(hs: ArrayOrFloat) -> np.ndarray | int:
    """Reclass G: Hillshade (0..255) -> 200 (sombreado) o 100 (expuesto)."""
    hs_arr = np.asarray(hs, dtype=float)
    res = np.where(hs_arr <= RECLASS_G_CORTE, CODIGO_SOMBREADO, CODIGO_EXPUESTO).astype(np.int16)
    if np.isscalar(hs):
        return int(res.item())
    return res


def clave_compuesta(hcfm_pct: ArrayOrFloat,
                    temp_c: ArrayOrFloat,
                    hs: ArrayOrFloat,
                    modo_seguro: bool = True) -> np.ndarray | int:
    """Calcula la clave compuesta entera: ReclassC(HCFM) + ReclassG(HS) + ReclassA(T)."""
    c = reclass_c(hcfm_pct, modo_seguro=modo_seguro)
    g = reclass_g(hs)
    a = reclass_a(temp_c, modo_seguro=modo_seguro)
    clave = c + g + a

    if not modo_seguro:
        c_arr = np.asarray(c)
        a_arr = np.asarray(a)
        clave = np.where((c_arr == 0) | (a_arr == 0), 0, clave)

    if np.isscalar(hcfm_pct) and np.isscalar(temp_c) and np.isscalar(hs):
        return int(np.asarray(clave).item())
    return clave


def probabilidad_ignicion(temp_c: ArrayOrFloat,
                          hr_pct: ArrayOrFloat,
                          hs: ArrayOrFloat,
                          matriz: Optional[Dict[int, float]] = None,
                          modo_seguro: bool = True) -> ArrayOrFloat:
    """Traduce (T, HR, Hillshade) a Probabilidad de Ignición (%) usando la matriz de 288 celdas."""
    mat = MATRIZ_BASE_ROTHERMEL if matriz is None else matriz
    m = hcfm(hr_pct, temp_c)
    claves = clave_compuesta(m, temp_c, hs, modo_seguro=modo_seguro)

    claves_arr = np.asarray(claves, dtype=int)
    max_k = max(max(mat.keys()), int(claves_arr.max()) if claves_arr.size > 0 else 0)
    tabla = np.full(max_k + 1, np.nan, dtype=float)
    for k, v in mat.items():
        tabla[k] = v

    pi_arr = np.where(claves_arr > 0, tabla[np.clip(claves_arr, 0, max_k)], np.nan)
    if np.isscalar(temp_c) and np.isscalar(hr_pct) and np.isscalar(hs):
        return float(pi_arr.item())
    return pi_arr


def condicion_boton_rojo(pi_pct: ArrayOrFloat,
                         viento_kmh_val: ArrayOrFloat,
                         umbral_pi: float = UMBRAL_PI,
                         umbral_viento: float = UMBRAL_VIENTO_KMH) -> ArrayOrFloat:
    """Evalúa la regla de activación: (PI >= umbral_pi) AND (Viento >= umbral_viento)."""
    pi_arr = np.asarray(pi_pct, dtype=float)
    v_arr = np.asarray(viento_kmh_val, dtype=float)
    res = (pi_arr >= umbral_pi) & (v_arr >= umbral_viento)
    if np.isscalar(pi_pct) and np.isscalar(viento_kmh_val):
        return bool(res.item())
    return res


def acumulacion_horas_br(condiciones_horarias: np.ndarray) -> np.ndarray:
    """Calcula el número de pasos horarios (0..5) en condición Botón Rojo.

    Parameters
    ----------
    condiciones_horarias : Array booleano de forma (5, ...) correspondiente a las 5 horas de la tarde.
    """
    arr = np.asarray(condiciones_horarias, dtype=bool)
    return arr.sum(axis=0).astype(np.int16)
