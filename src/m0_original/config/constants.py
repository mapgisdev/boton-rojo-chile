# -*- coding: utf-8 -*-
"""
src/m0_original/config/constants.py — Constantes operacionales y parámetros congelados de M0.
"""

from __future__ import annotations

# Umbrales críticos oficiales CONAF (confirmados en metadatos y publicaciones)
UMBRAL_PI = 70.0          # Probabilidad de ignición mínima (%)
UMBRAL_VIENTO_KMH = 20.0  # Velocidad de viento mínima a 10 m (km/h)

# Ventana vespertina crítica (5 pasos horarios: 14, 15, 16, 17, 18)
HORA_INICIO = 14          # Hora local inicial
HORA_FIN = 18             # Hora local final (18:00–18:59)
PASOS_HORARIOS = 5

# Horizonte de pronóstico publicado por CONAF
DIAS_PRONOSTICO = 5       # d0 a d4

# Clases de la cobertura ESA WorldCover 2021 v200 consideradas superficie combustible
CLASES_COMBUSTIBLE = (10, 20, 30, 40, 90)

# Parámetros del Hillshade topográfico SRTM 90 m en el modelo original
HILLSHADE_AZIMUT = 313.0   # Azimut solar en grados (noroeste)
HILLSHADE_ALTITUD = 60.0   # Ángulo de elevación solar sobre el horizonte en grados

# Códigos de exposición solar Reclass G
CODIGO_EXPUESTO = 100
CODIGO_SOMBREADO = 200
RECLASS_G_CORTE = 123.5

# Escalas espaciales verificadas empíricamente
ESCALA_INDICE_M = 2000     # Malla de cálculo nominal (4.000.000 m²)
ESCALA_ZONAL_M = 500       # Unidad de cuantización de com_ha (25 ha)

# Huso horario dinámico de Chile continental
TIMEZONE_CHILE = "America/Santiago"
