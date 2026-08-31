# -*- coding: utf-8 -*-
"""
src/m0_original — Réplica independiente y congelada del Botón Rojo Original CONAF (Línea Base M0).

Versión congelada: 1.0.0
"""

from __future__ import annotations

M0_VERSION = "1.0.0"
M0_FROZEN = True

from src.m0_original.config.constants import (
    CLASES_COMBUSTIBLE,
    DIAS_PRONOSTICO,
    ESCALA_INDICE_M,
    ESCALA_ZONAL_M,
    HORA_FIN,
    HORA_INICIO,
    UMBRAL_PI,
    UMBRAL_VIENTO_KMH,
)
from src.m0_original.hcfm.fuel_moisture import hcfm
from src.m0_original.meteorology.wind import viento_kmh
from src.m0_original.terrain.hillshade import hillshade
from src.m0_original.reclass.tables import (
    reclass_a,
    reclass_b,
    reclass_c,
    reclass_d,
    reclass_e,
    reclass_f,
    reclass_g,
)
from src.m0_original.ignition_matrix.rothermel_engine import (
    pi_continua_rothermel,
    construir_matriz_pi,
)
from src.m0_original.ignition_matrix.matrix_loader import (
    MATRIZ_PI_ROTHERMEL,
    clave_pi,
    probabilidad_ignicion,
)
from src.m0_original.hourly.activation import condicion_boton_rojo
from src.m0_original.daily.accumulation import horas_boton_rojo
from src.m0_original.fuels.mask import mascara_combustible
from src.m0_original.commune.zonal_reduction import reducir_comunal

__all__ = [
    "M0_VERSION",
    "M0_FROZEN",
    "UMBRAL_PI",
    "UMBRAL_VIENTO_KMH",
    "HORA_INICIO",
    "HORA_FIN",
    "DIAS_PRONOSTICO",
    "ESCALA_INDICE_M",
    "ESCALA_ZONAL_M",
    "CLASES_COMBUSTIBLE",
    "hcfm",
    "viento_kmh",
    "hillshade",
    "reclass_a",
    "reclass_b",
    "reclass_c",
    "reclass_d",
    "reclass_e",
    "reclass_f",
    "reclass_g",
    "pi_continua_rothermel",
    "construir_matriz_pi",
    "MATRIZ_PI_ROTHERMEL",
    "clave_pi",
    "probabilidad_ignicion",
    "condicion_boton_rojo",
    "horas_boton_rojo",
    "mascara_combustible",
    "reducir_comunal",
]
