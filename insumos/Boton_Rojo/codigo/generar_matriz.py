# -*- coding: utf-8 -*-
"""
generar_matriz.py — Genera la matriz reconstruida de Probabilidad de Ignicion
en tres formatos: Excel legible, arreglos JavaScript para Google Earth Engine y
tabla larga en CSV.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from nucleo import (MATRIZ_PI, RECLASS_A_ETIQUETAS, RECLASS_C_VALORES,
                    RECLASS_A_REPRESENTANTE, construir_matriz_pi,
                    CODIGO_EXPUESTO, CODIGO_SOMBREADO, UMBRAL_PI)

ETIQUETAS_HCFM = {
    2000: "<= 2", 3000: "2 - 3", 4000: "3 - 4", 5000: "4 - 5", 6000: "5 - 6",
    7000: "6 - 7", 8000: "7 - 8", 9000: "8 - 9", 10000: "9 - 10", 11000: "10 - 11",
    12000: "11 - 12", 13000: "12 - 13", 14000: "13 - 14", 15000: "14 - 15",
    16000: "15 - 16", 17000: "> 16",
}


def tabla_larga(matriz=None) -> pd.DataFrame:
    matriz = MATRIZ_PI if matriz is None else matriz
    filas = []
    for clave, valor in sorted(matriz.items()):
        clave_c = (clave // 1000) * 1000
        resto = clave - clave_c
        codigo_sombra = (resto // 100) * 100
        clase_t = resto - codigo_sombra
        filas.append({
            "clave": clave,
            "clave_hcfm": clave_c,
            "hcfm_pct": ETIQUETAS_HCFM[clave_c],
            "sombreado": "Sombreado" if codigo_sombra == CODIGO_SOMBREADO else "Expuesto",
            "clase_temperatura": int(clase_t),
            "temperatura_c": RECLASS_A_ETIQUETAS[int(clase_t) - 1],
            "probabilidad_ignicion_pct": valor,
            "activa_umbral_70": valor >= UMBRAL_PI,
        })
    return pd.DataFrame(filas)


def tabla_ancha(matriz=None, codigo_sombra: int = CODIGO_EXPUESTO) -> pd.DataFrame:
    matriz = MATRIZ_PI if matriz is None else matriz
    datos = {}
    for clave_c in RECLASS_C_VALORES:
        fila = {}
        for clase_t, etiqueta in enumerate(RECLASS_A_ETIQUETAS, start=1):
            fila[etiqueta] = matriz[clave_c + codigo_sombra + clase_t]
        datos[ETIQUETAS_HCFM[clave_c]] = fila
    df = pd.DataFrame(datos).T
    df.index.name = "HCFM (%)"
    return df


def a_javascript(matriz=None) -> str:
    matriz = MATRIZ_PI if matriz is None else matriz
    claves = sorted(matriz)
    valores = [matriz[k] for k in claves]
    return ("// Matriz reconstruida de Probabilidad de Ignicion (288 celdas).\n"
            "// clave = ReclassC(HCFM) + ReclassG(hillshade) + ReclassA(T)\n"
            "var CLAVES_PI = " + json.dumps(claves) + ";\n"
            "var VALORES_PI = " + json.dumps(valores) + ";\n")


if __name__ == "__main__":
    larga = tabla_larga()
    larga.to_csv("matriz_probabilidad_ignicion.csv", index=False)

    variantes = {
        "Reconstruida (base)": MATRIZ_PI,
        "Variante seca (-1 pp)": construir_matriz_pi(desfase_hcfm=-1.0),
        "Variante posicional NWCG": construir_matriz_pi(
            temperaturas=[1.7, 7.2, 12.8, 18.3, 23.9, 29.4, 35.0, 40.6, 46.1]),
    }

    with pd.ExcelWriter("matriz_probabilidad_ignicion.xlsx", engine="openpyxl") as xw:
        larga.to_excel(xw, sheet_name="Matriz 288 celdas", index=False)
        tabla_ancha(codigo_sombra=CODIGO_EXPUESTO).to_excel(xw, sheet_name="Expuesto")
        tabla_ancha(codigo_sombra=CODIGO_SOMBREADO).to_excel(xw, sheet_name="Sombreado")
        comparacion = pd.DataFrame({
            nombre: pd.Series({k: v for k, v in m.items()})
            for nombre, m in variantes.items()})
        comparacion.index.name = "clave"
        comparacion.reset_index().to_excel(xw, sheet_name="Variantes", index=False)

    with open("matriz_pi.js", "w", encoding="utf-8") as fh:
        fh.write(a_javascript())

    print("Archivos generados:")
    print("  matriz_probabilidad_ignicion.csv   ", len(larga), "filas")
    print("  matriz_probabilidad_ignicion.xlsx  ", "4 hojas")
    print("  matriz_pi.js                       ", "arreglos para Earth Engine")
    print()
    print("Celdas que superan el umbral de 70 %, por variante:")
    for nombre, m in variantes.items():
        print(f"  {nombre:28s} {sum(1 for v in m.values() if v >= UMBRAL_PI):3d} / 288")
    print()
    print("Matriz reconstruida, condicion EXPUESTO (PI en %):")
    print(tabla_ancha().to_string())
