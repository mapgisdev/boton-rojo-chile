# -*- coding: utf-8 -*-
"""
src/m0_original/ignition_matrix/empirical_inversion.py — Inversión empírica de la matriz oficial CONAF.
"""

from __future__ import annotations

from typing import Callable, Dict, Optional, Tuple
import pandas as pd


def invertir_matriz_desde_capas(
    df_puntos: pd.DataFrame,
    col_clase_tp: str = "clase_tp",
    col_clase_hc: str = "clase_hc",
    col_sombreado: str = "sombreado",
    col_decil_pi: str = "decil_pi",
) -> pd.DataFrame:
    """Tabula la moda empírica del decil de PI a partir de muestras espaciales cruzadas.

    Parameters
    ----------
    df_puntos : pd.DataFrame
        DataFrame con las muestras espaciales de las capas TP, HC, PI y Sombreado.
    col_clase_tp : str
        Nombre de la columna con la clase de temperatura (1..9).
    col_clase_hc : str
        Nombre de la columna con la clase de HCFM (1..10 o millares).
    col_sombreado : str
        Nombre de la columna de sombreado (100 = expuesto, 200 = sombreado).
    col_decil_pi : str
        Nombre de la columna con el decil de PI publicado por CONAF.

    Returns
    -------
    pd.DataFrame
        Tabla con la moda, mínimo, máximo y número de muestras por combinación.
    """
    df_clean = df_puntos.dropna(
        subset=[col_clase_tp, col_clase_hc, col_sombreado, col_decil_pi]
    )
    if df_clean.empty:
        return pd.DataFrame()

    agrupado = (
        df_clean.groupby(
            [col_clase_hc, col_clase_tp, col_sombreado], dropna=False
        )[col_decil_pi]
        .agg(
            decil_moda=lambda s: s.mode().iat[0] if len(s.mode()) > 0 else None,
            decil_min="min",
            decil_max="max",
            n="size",
        )
        .reset_index()
    )
    return agrupado.sort_values([col_clase_hc, col_clase_tp]).reset_index(
        drop=True
    )
