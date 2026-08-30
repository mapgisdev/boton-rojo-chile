"""
src/baseline/pi_matrix.py — Matriz de Probabilidad de Ignición de 288 celdas (Rothermel / BehavePlus / NWCG).

Ecuación física original:
    Schroeder (1969), Rothermel (1983), implementada en ignite.cpp (RMRS Missoula, USDA Forest Service).
"""

from __future__ import annotations

from typing import Dict, List, Optional
import numpy as np

from src.baseline.tables import (
    CODIGO_EXPUESTO,
    CODIGO_SOMBREADO,
    RECLASS_A_REPRESENTANTE,
    RECLASS_C_VALORES,
)


def pi_continua_rothermel(temp_c: float | np.ndarray,
                          hcfm_pct: float | np.ndarray,
                          sombreado: float | np.ndarray) -> float | np.ndarray:
    """Calcula la probabilidad de ignición (%) según la ecuación física de Rothermel / BehavePlus.

    Parameters
    ----------
    temp_c : Temperatura del aire en °C.
    hcfm_pct : Humedad del combustible fino muerto en % (base peso seco).
    sombreado : Fracción de sombreado en [0, 1] (0.0 = pleno sol / expuesto, 1.0 = sombreado).

    Returns
    -------
    Probabilidad de ignición continua en el rango [0.0, 100.0] %.
    """
    temp_c_arr = np.asarray(temp_c, dtype=float)
    hcfm_arr = np.asarray(hcfm_pct, dtype=float)
    sombra_arr = np.clip(np.asarray(sombreado, dtype=float), 0.0, 1.0)

    # 1. Temperatura del combustible en Fahrenheit
    temp_f = temp_c_arr * 9.0 / 5.0 + 32.0
    tf_comb = temp_f + (25.0 - 20.0 * sombra_arr)
    tc_comb = (tf_comb - 32.0) * 5.0 / 9.0

    # 2. Humedad fraccional
    m = hcfm_arr / 100.0

    # 3. Calor de ignición requerido (Qig)
    qig = (
        144.51
        - 0.26600 * tc_comb
        - 0.00058 * (tc_comb ** 2)
        - tc_comb * m
        + 18.5400 * (1.0 - np.exp(-15.1 * m))
        + 640.0 * m
    )
    qig = np.minimum(qig, 400.0)

    # 4. Potencia de ignición y probabilidad
    x = 0.1 * (400.0 - qig)
    p = 0.000048 * np.power(np.maximum(x, 0.0), 4.3) / 50.0
    result = np.clip(p, 0.0, 1.0) * 100.0

    if np.isscalar(temp_c) and np.isscalar(hcfm_pct) and np.isscalar(sombreado):
        return float(result)
    return result


def construir_matriz_rothermel(desfase_hcfm: float = 0.0,
                               temperaturas: Optional[List[float]] = None) -> Dict[int, float]:
    """Genera el diccionario de 288 celdas: clave_compuesta -> PI_pct.

    Clave compuesta = ReclassC (2000..17000) + ReclassG (100 | 200) + ReclassA (1..9).
    """
    temps = RECLASS_A_REPRESENTANTE if temperaturas is None else temperaturas
    matriz: Dict[int, float] = {}

    for clave_c in RECLASS_C_VALORES:
        hcfm_rep = max(0.5, (clave_c / 1000.0) + desfase_hcfm)
        for cod_sombra, sombra_val in ((CODIGO_EXPUESTO, 0.0), (CODIGO_SOMBREADO, 1.0)):
            for clase_t, temp_rep in enumerate(temps, start=1):
                clave = clave_c + cod_sombra + clase_t
                val_pi = float(pi_continua_rothermel(temp_rep, hcfm_rep, sombra_val))
                matriz[clave] = round(val_pi, 1)

    return matriz


# Instancia por defecto congelada del baseline
MATRIZ_BASE_ROTHERMEL: Dict[int, float] = construir_matriz_rothermel()
