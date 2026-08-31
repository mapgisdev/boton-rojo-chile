# -*- coding: utf-8 -*-
"""
src/m0_original/ignition_matrix/rothermel_engine.py — Motor físico de probabilidad de ignición (Rothermel/BehavePlus).
"""

from __future__ import annotations

from typing import Dict, List, Optional
import numpy as np

from src.m0_original.config.constants import CODIGO_EXPUESTO, CODIGO_SOMBREADO
from src.m0_original.reclass.tables import (
    RECLASS_A_REPRESENTANTE,
    RECLASS_C_VALORES,
)


def pi_continua_rothermel(temp_c, hcfm_pct, sombreado):
    """Calcula la Probabilidad de Ignición (%) por la ecuación de Rothermel/BehavePlus.

    Fuente: `ignite.cpp` de la biblioteca BEHAVE (Rocky Mountain Research Station, USFS Missoula; Schroeder 1969).
    Es la ecuación física que genera la tabla oficial del NWCG (IRPG).

    Parameters
    ----------
    temp_c : float o array-like
        Temperatura del aire a 2 m en grados Celsius.
    hcfm_pct : float o array-like
        Humedad del combustible fino muerto en % (base peso seco).
    sombreado : float o array-like
        Fracción de sombreado [0.0 = expuesto al sol, 1.0 = sombreado total].

    Returns
    -------
    float o np.ndarray
        Probabilidad de ignición continua en % (rango 0 a 100).
    """
    temp_c = np.asarray(temp_c, dtype=float)
    m = np.asarray(hcfm_pct, dtype=float) / 100.0
    sombra = np.clip(np.asarray(sombreado, dtype=float), 0.0, 1.0)

    # 1. Temperatura del combustible (ajuste por radiación solar)
    temp_f = temp_c * 9.0 / 5.0 + 32.0
    tf_comb = temp_f + (25.0 - 20.0 * sombra)
    tc_comb = (tf_comb - 32.0) * 5.0 / 9.0

    # 2. Calor de pre-ignición (Qig)
    qig = (
        144.51
        - 0.26600 * tc_comb
        - 0.00058 * tc_comb**2
        - tc_comb * m
        + 18.5400 * (1.0 - np.exp(-15.1 * m))
        + 640.0 * m
    )
    qig = np.minimum(qig, 400.0)

    # 3. Probabilidad de ignición
    x = 0.1 * (400.0 - qig)
    p = 0.000048 * np.power(np.maximum(x, 0.0), 4.3) / 50.0
    return np.clip(p, 0.0, 1.0) * 100.0


def construir_matriz_pi(
    redondear_a_decena: bool = False,
    desfase_hcfm: float = 0.0,
    temperaturas: Optional[List[float]] = None,
) -> Dict[int, float]:
    """Construye la matriz de 288 celdas: Clave Compuesta -> PI (%).

    Clave = ReclassC(HCFM) + ReclassG(Hillshade) + ReclassA(T).
    Ejemplo: 5000 + 100 + 8 = 5108 (HCFM 4-5 %, Expuesto, T 30-35 °C).

    16 niveles HCFM x 2 exposiciones x 9 clases Temperatura = 288 combinaciones.

    Parameters
    ----------
    redondear_a_decena : bool
        Si True, redondea a la decena más cercana, replicando la tabla impresa NWCG.
    desfase_hcfm : float
        Ajuste fino de la humedad representativa de cada clase de millares.
    temperaturas : List[float], opcional
        Temperaturas representativas de las 9 clases de Reclass A.

    Returns
    -------
    Dict[int, float]
        Diccionario con las 288 claves enteras y sus valores de PI.
    """
    temps = RECLASS_A_REPRESENTANTE if temperaturas is None else temperaturas
    matriz: Dict[int, float] = {}

    for clave_c in RECLASS_C_VALORES:
        hcfm_rep = max(0.5, clave_c / 1000.0 + desfase_hcfm)
        for cod_sombra, sombra_val in (
            (CODIGO_EXPUESTO, 0.0),
            (CODIGO_SOMBREADO, 1.0),
        ):
            for clase_t, temp_rep in enumerate(temps, start=1):
                valor = float(pi_continua_rothermel(temp_rep, hcfm_rep, sombra_val))
                if redondear_a_decena:
                    valor = float(round(valor, -1))
                clave = clave_c + cod_sombra + clase_t
                matriz[clave] = round(valor, 1)

    return matriz
