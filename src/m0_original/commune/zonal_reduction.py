# -*- coding: utf-8 -*-
"""
src/m0_original/commune/zonal_reduction.py — Reducción zonal y cálculo de métricas comunales oficiales (SUM_br_ha, com_ha, proportion).
"""

from __future__ import annotations

from typing import Dict, List, Optional
import numpy as np
import pandas as pd


def reducir_comunal(
    horas_por_dia: Dict[str, np.ndarray],
    raster_comunas: np.ndarray,
    raster_area_ha: np.ndarray,
    mascara_comb: np.ndarray,
    dict_comunas: Dict[int, Dict[str, str]],
    campo_id: str = "com_id",
    campo_nombre: str = "com",
    campo_prov: str = "prov",
    campo_reg: str = "reg",
) -> pd.DataFrame:
    """Ejecuta la reducción zonal comunal oficial para cada fecha, comuna y clase de horas.

    Parameters
    ----------
    horas_por_dia : Dict[str, np.ndarray]
        Mapeo {fecha_iso: array_2d_horas_0a5}.
    raster_comunas : np.ndarray
        Array 2D con el índice entero de cada comuna (0 = fuera de territorio).
    raster_area_ha : np.ndarray
        Array 2D con la superficie en hectáreas de cada celda.
    mascara_comb : np.ndarray
        Array 2D booleano de combustible.
    dict_comunas : Dict[int, Dict[str, str]]
        Mapeo de índice entero a metadatos de la comuna (id, nombre, provincia, región).
    campo_id : str
        Nombre del campo de ID comunal.
    campo_nombre : str
        Nombre del campo de nombre de comuna.

    Returns
    -------
    pd.DataFrame
        Tabla relacional idéntica a la publicada por CONAF.
    """
    combustible = mascara_comb.astype(bool)

    # 1. Precomputar superficie combustible total por comuna (com_ha)
    superficie_combustible: Dict[int, float] = {}
    for idx in dict_comunas:
        en_comuna = raster_comunas == idx
        ha_comb = float(raster_area_ha[en_comuna & combustible].sum())
        superficie_combustible[idx] = round(ha_comb, 2)

    filas: List[Dict] = []

    # 2. Reducción por día y por categoría de horas (1 a 5)
    for fecha, arr_horas in sorted(horas_por_dia.items()):
        for h in range(1, 6):
            activos_h = (arr_horas == h) & combustible
            if not np.any(activos_h):
                continue

            for idx, meta in dict_comunas.items():
                sel = activos_h & (raster_comunas == idx)
                if not np.any(sel):
                    continue

                sum_ha = round(float(raster_area_ha[sel].sum()), 2)
                com_ha = superficie_combustible.get(idx, 0.0)
                prop = round(sum_ha / com_ha, 4) if com_ha > 0 else np.nan

                filas.append(
                    {
                        "date": fecha,
                        "com_id": meta.get(campo_id, idx),
                        "com": meta.get(campo_nombre, f"Comuna_{idx}"),
                        "prov": meta.get(campo_prov, ""),
                        "reg": meta.get(campo_reg, ""),
                        "horas": h,
                        "SUM_br_ha": sum_ha,
                        "com_ha": com_ha,
                        "proportion": prop,
                    }
                )

    if not filas:
        return pd.DataFrame(
            columns=[
                "date",
                "com_id",
                "com",
                "prov",
                "reg",
                "horas",
                "SUM_br_ha",
                "com_ha",
                "proportion",
            ]
        )

    df = pd.DataFrame(filas)
    return df.sort_values(["date", "com_id", "horas"]).reset_index(drop=True)
