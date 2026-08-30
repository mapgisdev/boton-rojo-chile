"""
Módulo baseline M0 — BR-CONAF (Réplica inmutable del sistema original).
"""

from src.baseline.conaf_core import (
    acumulacion_horas_br,
    clave_compuesta,
    condicion_boton_rojo,
    hcfm,
    hillshade,
    probabilidad_ignicion,
    reclass_a,
    reclass_c,
    reclass_g,
    viento_kmh,
)
from src.baseline.pi_matrix import MATRIZ_BASE_ROTHERMEL, construir_matriz_rothermel
from src.baseline.tables import (
    CLASES_COMBUSTIBLE,
    DIAS_PRONOSTICO,
    HILLSHADE_ALTITUD,
    HILLSHADE_AZIMUT,
    HORA_FIN_VENTANA,
    HORA_INICIO_VENTANA,
    UMBRAL_PI,
    UMBRAL_VIENTO_KMH,
)

__all__ = [
    "hcfm",
    "viento_kmh",
    "hillshade",
    "reclass_a",
    "reclass_c",
    "reclass_g",
    "clave_compuesta",
    "probabilidad_ignicion",
    "condicion_boton_rojo",
    "acumulacion_horas_br",
    "MATRIZ_BASE_ROTHERMEL",
    "construir_matriz_rothermel",
    "CLASES_COMBUSTIBLE",
    "DIAS_PRONOSTICO",
    "HILLSHADE_ALTITUD",
    "HILLSHADE_AZIMUT",
    "HORA_FIN_VENTANA",
    "HORA_INICIO_VENTANA",
    "UMBRAL_PI",
    "UMBRAL_VIENTO_KMH",
]
