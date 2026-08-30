"""
src/baseline/tables.py — Tablas de reclasificación oficiales del modelo Botón Rojo CONAF (Reclass A-G).

Fuente: NASA DEVELOP 2022 (Technical Paper NTRS 20220005936 y Code Tutorial 20220007384),
        verificado contra metadatos y servicios publicados de CONAF / GEPRIF.
"""

from typing import Final, List, Tuple

# Constantes operacionales
UMBRAL_PI: Final[float] = 70.0  # % probabilidad de ignición mínima
UMBRAL_VIENTO_KMH: Final[float] = 20.0  # km/h velocidad de viento mínima a 10m
HORA_INICIO_VENTANA: Final[int] = 14  # 14:00 hora local
HORA_FIN_VENTANA: Final[int] = 18  # 18:59 hora local (5 pasos horarios: 14, 15, 16, 17, 18)
DIAS_PRONOSTICO: Final[int] = 5  # d0 a d4

# Clases de cobertura ESA WorldCover v200 (2021) consideradas superficie combustible:
# 10: Bosques (Tree cover)
# 20: Matorrales (Shrubland)
# 30: Pastizales (Grassland)
# 40: Cultivos agrícolas (Cropland)
# 90: Humedales herbáceos (Herbaceous wetland / Mangroves)
CLASES_COMBUSTIBLE: Final[Tuple[int, ...]] = (10, 20, 30, 40, 90)

# Parámetros de sombreado topográfico (Hillshade SRTM 90m en ArcGIS / GEE)
HILLSHADE_AZIMUT: Final[float] = 313.0
HILLSHADE_ALTITUD: Final[float] = 60.0

# ---------------------------------------------------------------------------
# Tablas de reclasificación Reclass A - G
# ---------------------------------------------------------------------------

# Reclass A — Temperatura (°C) -> clase 1..9
# Cortes: <0 -> 1; 0-5 -> 2; 5-10 -> 3; 10-15 -> 4; 15-20 -> 5;
#         20-25 -> 6; 25-30 -> 7; 30-35 -> 8; >35 -> 9
RECLASS_A_CORTES: Final[List[float]] = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0]
RECLASS_A_ETIQUETAS: Final[List[str]] = [
    "Menor a 0", "0 - 5", "5 - 10", "10 - 15", "15 - 20",
    "20 - 25", "25 - 30", "30 - 35", "Mayor a 35"
]
RECLASS_A_REPRESENTANTE: Final[List[float]] = [-2.5, 2.5, 7.5, 12.5, 17.5, 22.5, 27.5, 32.5, 37.5]

# Reclass B — HCFM (%) -> clase 1..10 (Leyenda capa pública HC)
RECLASS_B_CORTES: Final[List[float]] = [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 15.0, 20.0, 25.0]
RECLASS_B_ETIQUETAS: Final[List[str]] = [
    "0 - 2", "2 - 4", "4 - 6", "6 - 8", "8 - 10", "10 - 12",
    "12 - 15", "15 - 20", "20 - 25", "Mayor a 25"
]

# Reclass C — HCFM (%) -> clave de millares 2000..17000
# Equivale a 1000 * ceil(HCFM), acotado a [2000, 17000]
RECLASS_C_CORTES: Final[List[float]] = [
    2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0,
    10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 30.0
]
RECLASS_C_VALORES: Final[List[int]] = [
    2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000,
    10000, 11000, 12000, 13000, 14000, 15000, 16000, 17000
]

# Reclass D — Probabilidad de ignición (%) -> deciles 10, 20, ..., 100
RECLASS_D_CORTES: Final[List[float]] = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]

# Reclass E — Viento (km/h) -> clase 1..8 (Leyenda capa pública VV)
RECLASS_E_CORTES: Final[List[float]] = [3.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 10000.0]
RECLASS_E_ETIQUETAS: Final[List[str]] = [
    "Calmo", "3 - 5", "5 - 10", "10 - 15", "15 - 20",
    "20 - 25", "25 - 30", "Mayor a 30"
]

# Reclass G — Hillshade -> 200 si sombreado (<= 123.5), 100 si expuesto (> 123.5)
RECLASS_G_CORTE: Final[float] = 123.5
CODIGO_SOMBREADO: Final[int] = 200
CODIGO_EXPUESTO: Final[int] = 100
