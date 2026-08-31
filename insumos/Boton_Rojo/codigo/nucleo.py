# -*- coding: utf-8 -*-
"""
nucleo.py — Algoritmo del indice "Boton Rojo" de CONAF, reconstruido.

Implementacion pura (numpy, sin I/O) de la cadena de calculo:

    GFS (T, HR, u10, v10)
        -> HCFM  (humedad del combustible fino muerto, %)
        -> clave compuesta  = ReclassC(HCFM) + ReclassG(hillshade) + ReclassA(T)
        -> MATRIZ_PI[clave] = Probabilidad de Ignicion (%)
        -> Boton Rojo = (PI >= 70) AND (viento >= 20 km/h)
        -> horas = N de pasos horarios en 14:00-18:59 que cumplen la condicion

Trazabilidad de cada componente:

  [CONFIRMADO]  Umbrales, ventana horaria, fuente meteorologica (GFS de NOAA),
                mascara de combustible (Copernicus/ESA Landcover 2021).
                Fuente: metadatos oficiales del item ArcGIS Online
                41ee3c691359437aa9df2a09d7f6124e (owner: deigeprif, CONAF) y
                https://www.conaf.cl/incendios/situacion-actual-y-pronostico-de-incendios/

  [CONFIRMADO]  Formula HCFM, formula de viento, uso de hillshade SRTM y las
                siete tablas de reclasificacion (Reclass A-G).
                Fuente: NASA DEVELOP 2022, "Chile Disasters: Automating Wildfire
                Risk and Occurrence Mapping in Google Earth Engine",
                NTRS 20220005936 (Technical Paper) y 20220007384 (Code Tutorial),
                elaborado en conjunto con CONAF.

  [RECONSTRUIDO] La matriz de 288 celdas que traduce la clave compuesta a
                Probabilidad de Ignicion en %. CONAF no la publica. Aqui se
                reconstruye con la ecuacion de Probabilidad de Ignicion de
                Rothermel/BehavePlus (Schroeder 1969; ignite.cpp, RMRS Missoula),
                que reproduce la tabla oficial NWCG (IRPG) con error medio de
                0,83 puntos porcentuales. Debe calibrarse contra las capas
                publicadas por CONAF antes de uso operativo: ver conaf_api.py.

Autor: Unidad de Informacion y Analisis (UIA), CONAF.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

# ---------------------------------------------------------------------------
# Constantes operativas del Boton Rojo   [CONFIRMADO]
# ---------------------------------------------------------------------------

UMBRAL_PI = 70.0          # Probabilidad de ignicion minima, en %
UMBRAL_VIENTO_KMH = 20.0  # Velocidad del viento minima, en km/h
HORA_INICIO = 14          # Ventana de evaluacion: 14:00 ...
HORA_FIN = 18             # ... hasta 18:59 (5 pasos horarios) hora local de Chile
DIAS_PRONOSTICO = 5       # Horizonte publicado: d0 a d4

# Clases de la cobertura ESA WorldCover v200 (2021) consideradas "superficie
# combustible": 10 bosques, 20 matorrales, 30 pastizales, 40 cultivos agricolas,
# 90 humedales herbaceos.
CLASES_COMBUSTIBLE = (10, 20, 30, 40, 90)

# Parametros del hillshade en el modelo original de CONAF (ArcGIS): azimut 313,
# altura solar 60 grados.
HILLSHADE_AZIMUT = 313.0
HILLSHADE_ALTITUD = 60.0


# ---------------------------------------------------------------------------
# 1. Humedad del combustible fino muerto (HCFM)   [CONFIRMADO]
# ---------------------------------------------------------------------------

def hcfm(hr_pct, temp_c):
    """Humedad del combustible fino muerto, en % base peso seco.

    Regresion lineal desarrollada por la Universidad de Chile y utilizada por
    CONAF (NASA DEVELOP 2022, ecuacion 1):

        HCFM = 0,297374 + 0,262 * HR - 0,00982 * T

    Parameters
    ----------
    hr_pct : humedad relativa a 2 m, en % (1-100).
    temp_c : temperatura a 2 m, en grados Celsius.

    Nota: el Code Tutorial de NASA indica HR "entre 0 y 1"; el Technical Paper
    indica "percent value from 1-100". La correcta es 1-100: con HR = 50 % y
    T = 25 C se obtiene 13,15 %, valor fisicamente coherente, mientras que con
    HR en 0-1 se obtendria 0,18 %, imposible.
    """
    hr_pct = np.asarray(hr_pct, dtype=float)
    temp_c = np.asarray(temp_c, dtype=float)
    return 0.297374 + 0.262 * hr_pct - 0.00982 * temp_c


def viento_kmh(u10, v10):
    """Velocidad del viento a 10 m en km/h a partir de las componentes GFS en m/s.

        V = sqrt(u^2 + v^2) * 3,6                       [CONFIRMADO]
    """
    u10 = np.asarray(u10, dtype=float)
    v10 = np.asarray(v10, dtype=float)
    return np.hypot(u10, v10) * 3.6


def hillshade(dem, resolucion_m, azimut=HILLSHADE_AZIMUT, altitud=HILLSHADE_ALTITUD):
    """Sombreado topografico 0-255, equivalente a la funcion Hillshade de ArcGIS.

    CONAF lo calcula sobre el DEM SRTM de 90 m con azimut 313 y altura 60.
    """
    dem = np.asarray(dem, dtype=float)
    dy, dx = np.gradient(dem, resolucion_m, resolucion_m)
    pendiente = np.arctan(np.hypot(dx, dy))
    aspecto = np.arctan2(-dx, dy)
    az = np.deg2rad(360.0 - azimut + 90.0)
    zenit = np.deg2rad(90.0 - altitud)
    hs = (np.cos(zenit) * np.cos(pendiente)
          + np.sin(zenit) * np.sin(pendiente) * np.cos(az - aspecto))
    return np.clip(255.0 * hs, 0, 255)


# ---------------------------------------------------------------------------
# 2. Tablas de reclasificacion del modelo CONAF   [CONFIRMADO]
#    NASA DEVELOP 2022, Apendice A (Tablas A1 a A7).
# ---------------------------------------------------------------------------

# Reclass A — Temperatura (C) -> clase 1..9
RECLASS_A_CORTES = [0, 5, 10, 15, 20, 25, 30, 35, 40]
RECLASS_A_ETIQUETAS = ["Menor a 0", "0 - 5", "5 - 10", "10 - 15", "15 - 20",
                       "20 - 25", "25 - 30", "30 - 35", "Mayor a 35"]
# Representante de cada clase usado para reconstruir la matriz (punto medio;
# clase 1 y clase 9 se representan con -2,5 C y 37,5 C).
RECLASS_A_REPRESENTANTE = [-2.5, 2.5, 7.5, 12.5, 17.5, 22.5, 27.5, 32.5, 37.5]

# Reclass B — HCFM (%) -> clase 1..10. Es la leyenda de la capa publica "HC".
RECLASS_B_CORTES = [2, 4, 6, 8, 10, 12, 15, 20, 25]
RECLASS_B_ETIQUETAS = ["0 - 2", "2 - 4", "4 - 6", "6 - 8", "8 - 10", "10 - 12",
                       "12 - 15", "15 - 20", "20 - 25", "Mayor a 25"]

# Reclass C — HCFM (%) -> clave de millares 2000..17000.
# Equivale a 1000 * ceil(HCFM), acotado a [2000, 17000]: indexa las 16 filas de
# humedad de combustible fino muerto de la tabla NWCG de Probabilidad de Ignicion.
RECLASS_C_CORTES = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 30]
RECLASS_C_VALORES = [2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000,
                     10000, 11000, 12000, 13000, 14000, 15000, 16000, 17000]

# Reclass D — PI (%) -> decil 1..10. Es la leyenda de la capa publica "PI".
RECLASS_D_CORTES = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

# Reclass E — Viento (km/h) -> clase 1..8. Es la leyenda de la capa publica "VV".
RECLASS_E_CORTES = [3, 5, 10, 15, 20, 25, 30, 10000]
RECLASS_E_ETIQUETAS = ["Calmo", "3 - 5", "5 - 10", "10 - 15", "15 - 20",
                       "20 - 25", "25 - 30", "Mayor a 30"]

# Reclass F — Viento (km/h) -> binario del umbral de 20 km/h.
# Reclass G — Hillshade -> 200 si sombreado (0-123,5), 100 si expuesto (123,5-247).
RECLASS_G_CORTE = 123.5
CODIGO_SOMBREADO = 200
CODIGO_EXPUESTO = 100


def reclass_a(temp_c):
    """Temperatura (C) -> clase 1..9. Devuelve 0 fuera del dominio (T > 40 C)."""
    t = np.asarray(temp_c, dtype=float)
    clase = np.zeros(t.shape, dtype=np.int16)
    inferior = -np.inf
    for i, superior in enumerate(RECLASS_A_CORTES, start=1):
        clase = np.where((t > inferior) & (t <= superior), i, clase)
        inferior = superior
    return clase


def reclass_c(hcfm_pct):
    """HCFM (%) -> clave de millares 2000..17000. Devuelve 0 si HCFM > 30 %."""
    m = np.asarray(hcfm_pct, dtype=float)
    clave = np.zeros(m.shape, dtype=np.int32)
    inferior = 0.0
    for superior, valor in zip(RECLASS_C_CORTES, RECLASS_C_VALORES):
        clave = np.where((m > inferior) & (m <= superior), valor, clave)
        inferior = superior
    return clave


def reclass_g(hs):
    """Hillshade 0-255 -> 200 (sombreado) o 100 (expuesto)."""
    hs = np.asarray(hs, dtype=float)
    return np.where(hs <= RECLASS_G_CORTE, CODIGO_SOMBREADO, CODIGO_EXPUESTO).astype(np.int16)


def _clasificar(valores, cortes, etiquetas=None):
    """Utilidad generica: devuelve el indice 1..n de la clase de cada valor."""
    v = np.asarray(valores, dtype=float)
    clase = np.zeros(v.shape, dtype=np.int16)
    inferior = -np.inf
    for i, superior in enumerate(cortes, start=1):
        clase = np.where((v > inferior) & (v <= superior), i, clase)
        inferior = superior
    clase = np.where(v > cortes[-1], len(cortes), clase)
    return clase


def clase_hc(hcfm_pct):
    """Clase 1..10 de la capa publica HC de CONAF (Reclass B)."""
    return _clasificar(hcfm_pct, RECLASS_B_CORTES + [np.inf])


def clase_vv(viento):
    """Clase 1..8 de la capa publica VV de CONAF (Reclass E)."""
    return _clasificar(viento, RECLASS_E_CORTES)


def decil_pi(pi_pct):
    """Decil 10,20,...,100 tal como se publica en el campo `label` de la capa PI."""
    p = np.asarray(pi_pct, dtype=float)
    return (np.clip(np.ceil(p / 10.0), 1, 10) * 10).astype(np.int16)


# ---------------------------------------------------------------------------
# 3. Probabilidad de ignicion   [RECONSTRUIDO]
# ---------------------------------------------------------------------------

def pi_continua(temp_c, hcfm_pct, sombreado):
    """Probabilidad de ignicion (%) por la ecuacion de Rothermel/BehavePlus.

    Fuente: `ignite.cpp` de la biblioteca BEHAVE del Rocky Mountain Research
    Station (Missoula), dominio publico; deriva de Schroeder (1969) y es la
    ecuacion que genera la tabla de Probability of Ignition del NWCG (IRPG).

        Tf   = Taire + (25 - 20 * sombreado)          [F]  (temperatura del combustible)
        Tc   = (Tf - 32) * 5/9                        [C]
        m    = HCFM / 100                             [fraccion]
        Qig  = 144,51 - 0,266*Tc - 0,00058*Tc^2 - Tc*m
               + 18,54*(1 - exp(-15,1*m)) + 640*m
        Qig  = min(Qig, 400)
        x    = 0,1 * (400 - Qig)
        PI   = 100 * min(1, 0,000048 * x^4,3 / 50)

    Parameters
    ----------
    temp_c     : temperatura del AIRE, en grados Celsius.
    hcfm_pct   : humedad del combustible fino muerto, en %.
    sombreado  : fraccion 0-1 (0 = pleno sol, 1 = totalmente sombreado).
    """
    temp_c = np.asarray(temp_c, dtype=float)
    m = np.asarray(hcfm_pct, dtype=float) / 100.0
    sombra = np.clip(np.asarray(sombreado, dtype=float), 0.0, 1.0)

    temp_f = temp_c * 9.0 / 5.0 + 32.0
    tf_comb = temp_f + (25.0 - 20.0 * sombra)
    tc_comb = (tf_comb - 32.0) * 5.0 / 9.0

    qig = (144.51
           - 0.26600 * tc_comb
           - 0.00058 * tc_comb ** 2
           - tc_comb * m
           + 18.5400 * (1.0 - np.exp(-15.1 * m))
           + 640.0 * m)
    qig = np.minimum(qig, 400.0)
    x = 0.1 * (400.0 - qig)
    p = 0.000048 * np.power(np.maximum(x, 0.0), 4.3) / 50.0
    return np.clip(p, 0.0, 1.0) * 100.0


def construir_matriz_pi(redondear_a_decena: bool = False,
                        desfase_hcfm: float = 0.0,
                        temperaturas=None) -> Dict[int, float]:
    """Reconstruye la matriz de 288 celdas: clave compuesta -> PI en %.

    La clave es  ReclassC(HCFM) + ReclassG(hillshade) + ReclassA(T),
    p. ej. 5000 + 100 + 8 = 5108  (HCFM 4-5 %, expuesto, T 30-35 C).

    16 clases de HCFM x 2 condiciones de sombreado x 9 clases de temperatura = 288.

    Parameters
    ----------
    redondear_a_decena : redondea a la decena mas proxima, replicando la
        granularidad de la tabla impresa del NWCG.
    desfase_hcfm : ajuste de la humedad representativa de cada clase de
        millares. Por defecto 0,0, es decir clave 5000 -> HCFM 5 %. Con -1,0 se
        asume clave 5000 -> HCFM 4 % (borde inferior del intervalo), variante
        que produce una matriz sistematicamente mas seca y por tanto mas
        permisiva. Cual de las dos usa CONAF solo puede resolverse por
        calibracion empirica (ver conaf_api.calibrar_matriz).
    temperaturas : lista de 9 temperaturas representativas de las clases de
        Reclass A. Por defecto el punto medio de cada intervalo en C. Para
        ensayar la hipotesis de mapeo posicional sobre las columnas en F de la
        tabla NWCG, pasar [1.7, 7.2, 12.8, 18.3, 23.9, 29.4, 35.0, 40.6, 46.1].
    """
    temperaturas = RECLASS_A_REPRESENTANTE if temperaturas is None else temperaturas
    matriz: Dict[int, float] = {}
    for clave_c in RECLASS_C_VALORES:
        # La clave de millares indexa la fila de humedad de la tabla NWCG:
        # 2000 -> 2 %, 3000 -> 3 %, ..., 17000 -> 17 %.
        hcfm_rep = max(0.5, clave_c / 1000.0 + desfase_hcfm)
        for codigo_sombra, sombra in ((CODIGO_EXPUESTO, 0.0), (CODIGO_SOMBREADO, 1.0)):
            for clase_t, temp_rep in enumerate(temperaturas, start=1):
                valor = float(pi_continua(temp_rep, hcfm_rep, sombra))
                if redondear_a_decena:
                    valor = float(round(valor, -1))
                matriz[clave_c + codigo_sombra + clase_t] = round(valor, 1)
    return matriz


MATRIZ_PI = construir_matriz_pi()


def clave_pi(hcfm_pct, temp_c, hs):
    """Clave compuesta ReclassC + ReclassG + ReclassA. 0 = fuera de dominio."""
    c = reclass_c(hcfm_pct)
    g = reclass_g(hs)
    a = reclass_a(temp_c)
    clave = c + g + a
    return np.where((c == 0) | (a == 0), 0, clave).astype(np.int32)


def probabilidad_ignicion(temp_c, hr_pct, hs, matriz: Dict[int, float] = None):
    """Probabilidad de ignicion (%) por la via CONAF: HCFM -> clave -> matriz.

    Devuelve NaN donde la clave cae fuera del dominio de las tablas
    (T > 40 C o HCFM > 30 %), replicando el NoData del modelo original.
    """
    matriz = MATRIZ_PI if matriz is None else matriz
    m = hcfm(hr_pct, temp_c)
    claves = clave_pi(m, temp_c, hs)
    tabla = np.full(int(claves.max()) + 1 if claves.size else 1, np.nan)
    for k, v in matriz.items():
        if k < tabla.size:
            tabla[k] = v
    return np.where(claves > 0, tabla[np.clip(claves, 0, tabla.size - 1)], np.nan)


# ---------------------------------------------------------------------------
# 4. Regla de activacion y acumulacion horaria   [CONFIRMADO]
# ---------------------------------------------------------------------------

def condicion_boton_rojo(pi_pct, viento):
    """True donde PI >= 70 % Y viento >= 20 km/h (Reclass D + Reclass F, RFW == 2)."""
    pi_pct = np.asarray(pi_pct, dtype=float)
    viento = np.asarray(viento, dtype=float)
    return (pi_pct >= UMBRAL_PI) & (viento >= UMBRAL_VIENTO_KMH)


def horas_boton_rojo(condiciones_horarias):
    """Numero de pasos horarios (0..5) en condicion de Boton Rojo, por pixel.

    Parameters
    ----------
    condiciones_horarias : array booleano (n_horas, alto, ancho), con n_horas = 5
                           correspondientes a 14, 15, 16, 17 y 18 h local.
    """
    arr = np.asarray(condiciones_horarias, dtype=bool)
    return arr.sum(axis=0).astype(np.int16)


# ---------------------------------------------------------------------------
# 5. Autoverificacion
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 74)
    print("VERIFICACION 1 — Ecuacion PI contra la tabla oficial NWCG (sin sombra)")
    print("=" * 74)
    # Tabla NWCG de Probability of Ignition, condicion "unshaded".
    # Filas: temperatura de bulbo seco (F). Columnas: HCFM 2 % a 17 %.
    tabla_nwcg = {
        115: [100, 100, 80, 70, 60, 60, 50, 40, 40, 30, 30, 20, 20, 20, 20, 10],
        105: [100, 90, 80, 70, 60, 60, 50, 40, 40, 30, 30, 20, 20, 20, 10, 10],
        95:  [100, 90, 80, 70, 60, 50, 40, 40, 30, 30, 30, 20, 20, 20, 10, 10],
        85:  [100, 90, 80, 70, 60, 50, 40, 40, 30, 30, 20, 20, 20, 10, 10, 10],
        75:  [100, 80, 70, 60, 60, 50, 40, 40, 30, 30, 20, 20, 20, 10, 10, 10],
        65:  [90, 80, 70, 60, 50, 50, 40, 30, 30, 20, 20, 20, 20, 10, 10, 10],
        55:  [90, 80, 70, 60, 50, 40, 40, 30, 30, 20, 20, 20, 10, 10, 10, 10],
        45:  [90, 80, 70, 60, 50, 40, 40, 30, 30, 20, 20, 20, 10, 10, 10, 10],
        35:  [80, 70, 60, 50, 50, 40, 30, 30, 20, 20, 20, 10, 10, 10, 10, 10],
    }
    errores, exactos, total = [], 0, 0
    for tf, fila in tabla_nwcg.items():
        tc = (tf - 32) * 5 / 9
        for m, referencia in zip(range(2, 18), fila):
            calculado = round(float(pi_continua(tc, m, 0.0)), -1)
            errores.append(abs(calculado - referencia))
            exactos += int(calculado == referencia)
            total += 1
    print(f"  error medio = {sum(errores)/len(errores):.2f} pp"
          f" | maximo = {max(errores):.0f} pp"
          f" | coincidencias exactas = {exactos}/{total}")

    print()
    print("=" * 74)
    print("VERIFICACION 2 — Matriz reconstruida de 288 celdas")
    print("=" * 74)
    print(f"  celdas generadas: {len(MATRIZ_PI)}  (esperado: 16 x 2 x 9 = 288)")
    print(f"  celdas con PI >= 70 %: {sum(1 for v in MATRIZ_PI.values() if v >= 70)}")
    print(f"  ejemplo clave 5108 (HCFM 4-5 %, expuesto, T 30-35 C) = {MATRIZ_PI[5108]} %")
    print(f"  ejemplo clave 5208 (HCFM 4-5 %, sombreado, T 30-35 C) = {MATRIZ_PI[5208]} %")

    print()
    print("=" * 74)
    print("VERIFICACION 3 — Caso operativo tipo (Chile central, tarde de verano)")
    print("=" * 74)
    for t, h, v in [(32.0, 20.0, 25.0), (30.0, 25.0, 22.0), (35.0, 15.0, 30.0),
                    (28.0, 35.0, 25.0), (22.0, 45.0, 15.0)]:
        m = float(hcfm(h, t))
        pi = float(probabilidad_ignicion(np.array(t), np.array(h), np.array(200.0)))
        br = bool(condicion_boton_rojo(pi, v))
        print(f"  T={t:5.1f} C  HR={h:4.1f} %  V={v:4.1f} km/h"
              f" -> HCFM={m:5.2f} %  clase HC={int(clase_hc(m)):2d}"
              f"  PI={pi:5.1f} %  decil={int(decil_pi(pi)):3d}"
              f"  BOTON ROJO: {'SI' if br else 'NO'}")

    print()
    print("=" * 74)
    print("VERIFICACION 4 — Umbral de HR que activa el Boton Rojo (pleno sol)")
    print("=" * 74)
    for t in (20, 25, 30, 35, 40):
        umbral = None
        for hr in np.arange(60, 0, -0.1):
            pi = float(probabilidad_ignicion(np.array(float(t)), np.array(float(hr)),
                                             np.array(200.0)))
            if not np.isnan(pi) and pi >= UMBRAL_PI:
                umbral = hr
                break
        print(f"  T = {t:2d} C  ->  se requiere HR <= {umbral:4.1f} %"
              f"  (HCFM <= {float(hcfm(umbral, t)):.2f} %)")
