# -*- coding: utf-8 -*-
"""
conaf_api.py — Cliente de los servicios REST operacionales del Boton Rojo de CONAF.

Los productos del Boton Rojo se publican como Feature Services publicos en la
organizacion ArcGIS Online del Departamento de Desarrollo e Investigacion (DEI)
de la Gerencia de Proteccion contra Incendios Forestales (GEPRIF):

    https://services5.arcgis.com/A1ELWse9bRAi2JiV/arcgis/rest/services

Servicios relevantes (todos con 5 capas, d0 a d4, una por dia de pronostico,
nombradas dN_AAAAMMDD_XX y sobrescritas en cada corrida):

    TP  Temperatura (C)                        clases 1-9  (Reclass A)
    HR  Humedad relativa (%)
    HC  Humedad del combustible fino muerto (%) clases 1-10 (Reclass B)
    VV  Velocidad del viento (km/h)             clases 1-8  (Reclass E)
    PI  Probabilidad de ignicion (%)            deciles 10-100 (Reclass D)

    Boton_Rojo   Resultado agregado por comuna. Campos: date, horas (1-5),
                 com_id, com, prov, reg, nom_minrel, com_ha, SUM_br_ha,
                 proportion.

ADVERTENCIA OPERATIVA
---------------------
El servicio Boton_Rojo NO es un archivo historico: contiene unicamente la
ventana vigente de 5 dias y se sobrescribe en cada corrida. Para constituir una
serie historica hay que cosecharlo diariamente (funcion `cosechar`) o
solicitarlo formalmente al DEI/GEPRIF (dei.geprif@conaf.cl).

Licencia de los datos (declarada por CONAF en los metadatos del item):
"Los elementos y la informacion desplegada en este elemento son propiedad de
CONAF (...). Si bien los datos son de uso publico, en su utilizacion debera
citarse a CONAF como fuente de estos."

Requisitos: requests, pandas. Opcional para calibracion: geopandas, shapely.
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import date, datetime
from typing import Dict, Iterable, List, Optional

import pandas as pd
import requests

BASE = "https://services5.arcgis.com/A1ELWse9bRAi2JiV/arcgis/rest/services"
SERVICIOS_MET = ("TP", "HR", "HC", "VV", "PI")
SERVICIO_BR = "Boton_Rojo"
TIEMPO_ESPERA = 60
MAX_REGISTROS = 2000  # maxRecordCount declarado por el servicio

_PATRON_CAPA = re.compile(r"^d(\d)_(\d{8})_([A-Z]{2})$")


# ---------------------------------------------------------------------------
# Utilidades de bajo nivel
# ---------------------------------------------------------------------------

def _get(url: str, params: Dict) -> Dict:
    params = dict(params)
    params.setdefault("f", "json")
    respuesta = requests.get(url, params=params, timeout=TIEMPO_ESPERA)
    respuesta.raise_for_status()
    datos = respuesta.json()
    if isinstance(datos, dict) and "error" in datos:
        raise RuntimeError(f"Error del servicio ArcGIS: {datos['error']}")
    return datos


def listar_capas(servicio: str) -> pd.DataFrame:
    """Capas de un servicio, con su indice de dia y fecha de validez.

    >>> listar_capas("PI")
       id            nombre  dia       fecha var
        0  d0_20260826_PI    0  2026-08-26  PI
        ...
    """
    datos = _get(f"{BASE}/{servicio}/FeatureServer", {})
    filas = []
    for capa in datos.get("layers", []):
        nombre = capa.get("name", "")
        m = _PATRON_CAPA.match(nombre)
        filas.append({
            "id": capa["id"],
            "nombre": nombre,
            "dia": int(m.group(1)) if m else None,
            "fecha": datetime.strptime(m.group(2), "%Y%m%d").date() if m else None,
            "var": m.group(3) if m else None,
        })
    return pd.DataFrame(filas).sort_values("id").reset_index(drop=True)


def consultar(servicio: str, capa: int = 0, where: str = "1=1",
              campos: str = "*", geometria: bool = False,
              formato: str = "json") -> List[Dict]:
    """Consulta paginada completa de una capa. Devuelve la lista de features."""
    url = f"{BASE}/{servicio}/FeatureServer/{capa}/query"
    salida, desplazamiento = [], 0
    while True:
        params = {
            "where": where,
            "outFields": campos,
            "returnGeometry": str(geometria).lower(),
            "outSR": 4326,
            "resultOffset": desplazamiento,
            "resultRecordCount": MAX_REGISTROS,
            "f": "geojson" if formato == "geojson" else "json",
        }
        datos = _get(url, params)
        lote = datos.get("features", [])
        salida.extend(lote)
        if len(lote) < MAX_REGISTROS or not datos.get("exceededTransferLimit"):
            break
        desplazamiento += MAX_REGISTROS
        time.sleep(0.2)
    return salida


def _a_dataframe(features: List[Dict]) -> pd.DataFrame:
    if not features:
        return pd.DataFrame()
    if "properties" in features[0]:          # GeoJSON
        return pd.DataFrame([f["properties"] for f in features])
    return pd.DataFrame([f["attributes"] for f in features])


# ---------------------------------------------------------------------------
# Producto agregado por comuna
# ---------------------------------------------------------------------------

def descargar_boton_rojo() -> pd.DataFrame:
    """Ventana vigente de 5 dias del Boton Rojo, agregada por comuna.

    Columnas devueltas
    ------------------
    date        fecha de validez (AAAA-MM-DD)
    com_id      codigo unico territorial de la comuna
    com         nombre de la comuna
    prov, reg   provincia y region
    horas       numero de pasos horarios (1-5) de la ventana 14:00-18:59 en que
                el pixel cumplio simultaneamente PI >= 70 % y viento >= 20 km/h
    SUM_br_ha   superficie de la comuna, en hectareas, con ese numero de horas
    com_ha      superficie COMBUSTIBLE de la comuna, en hectareas
                (no la superficie total: verificado empiricamente, ver informe)
    proportion  SUM_br_ha / com_ha
    """
    columnas = ["date", "com_id", "com", "prov", "reg", "nom_minrel",
                "horas", "SUM_br_ha", "com_ha", "proportion"]
    df = _a_dataframe(consultar(SERVICIO_BR, 0, campos=",".join(columnas)))
    if df.empty:
        return df
    df = df[[c for c in columnas if c in df.columns]]
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df.sort_values(["date", "reg", "com", "horas"]).reset_index(drop=True)


def resumen_comunal(df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Una fila por comuna y dia: horas maximas y superficie total en condicion BR."""
    df = descargar_boton_rojo() if df is None else df
    if df.empty:
        return df
    resumen = (df.groupby(["date", "reg", "prov", "com", "com_id", "com_ha"],
                          as_index=False)
                 .agg(horas_max=("horas", "max"),
                      ha_boton_rojo=("SUM_br_ha", "sum")))
    resumen["proporcion_combustible"] = resumen["ha_boton_rojo"] / resumen["com_ha"]
    return resumen.sort_values(["date", "ha_boton_rojo"], ascending=[True, False])


# ---------------------------------------------------------------------------
# Cosecha diaria — construccion de la serie historica
# ---------------------------------------------------------------------------

def cosechar(directorio: str = "archivo_boton_rojo",
             servicios: Iterable[str] = (SERVICIO_BR,),
             con_geometria: bool = False) -> List[str]:
    """Descarga y archiva la corrida vigente. Pensada para ejecutarse a diario.

    Escribe, por cada servicio y capa, un archivo Parquet (o GeoJSON si se pide
    geometria) bajo `directorio/<servicio>/`, nombrado con la fecha de corrida y
    la fecha de validez. No sobrescribe archivos existentes, de modo que la
    ejecucion repetida es idempotente.

    Programacion sugerida (cron, 09:00 hora de Chile, de lunes a domingo):
        0 9 * * *  /usr/bin/python3 -c "import conaf_api; conaf_api.cosechar()"
    """
    os.makedirs(directorio, exist_ok=True)
    corrida = date.today().isoformat()
    escritos = []
    for servicio in servicios:
        destino = os.path.join(directorio, servicio)
        os.makedirs(destino, exist_ok=True)
        capas = listar_capas(servicio)
        for _, capa in capas.iterrows():
            etiqueta = capa["nombre"] or f"capa{capa['id']}"
            if con_geometria:
                ruta = os.path.join(destino, f"{corrida}__{etiqueta}.geojson")
                if os.path.exists(ruta):
                    continue
                features = consultar(servicio, int(capa["id"]), geometria=True,
                                     formato="geojson")
                with open(ruta, "w", encoding="utf-8") as fh:
                    json.dump({"type": "FeatureCollection", "features": features},
                              fh, ensure_ascii=False)
            else:
                ruta = os.path.join(destino, f"{corrida}__{etiqueta}.parquet")
                if os.path.exists(ruta):
                    continue
                df = _a_dataframe(consultar(servicio, int(capa["id"])))
                if df.empty:
                    continue
                df["_corrida"] = corrida
                df["_capa"] = etiqueta
                df.to_parquet(ruta, index=False)
            escritos.append(ruta)
            time.sleep(0.3)
    return escritos


def consolidar_archivo(directorio: str = "archivo_boton_rojo",
                       servicio: str = SERVICIO_BR) -> pd.DataFrame:
    """Une todos los Parquet cosechados en una sola tabla, sin duplicados.

    Ante varias corridas que pronostican la misma fecha, conserva la mas
    reciente (la de menor horizonte), que es la de mayor destreza.
    """
    destino = os.path.join(directorio, servicio)
    archivos = sorted(f for f in os.listdir(destino) if f.endswith(".parquet"))
    if not archivos:
        return pd.DataFrame()
    df = pd.concat([pd.read_parquet(os.path.join(destino, f)) for f in archivos],
                   ignore_index=True)
    if {"date", "com_id", "horas", "_corrida"} <= set(df.columns):
        df = (df.sort_values("_corrida")
                .drop_duplicates(subset=["date", "com_id", "horas"], keep="last"))
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Calibracion empirica de la matriz de probabilidad de ignicion
# ---------------------------------------------------------------------------

def calibrar_matriz(dia: int = 0, paso_grados: float = 0.05,
                    extension=(-75.7, -56.0, -66.4, -17.5),
                    dem_hillshade=None) -> pd.DataFrame:
    """Recupera empiricamente la matriz PI de CONAF cruzando sus capas publicadas.

    CONAF no publica la tabla de 288 valores que traduce la clave compuesta a
    probabilidad de ignicion; el Technical Paper de NASA DEVELOP (2022) senala
    que sus valores "were determined using the 2016-2017 fire season as a proxy",
    es decir que es una calibracion empirica chilena y no la tabla NFDRS. La
    unica via para recuperarla sin acceso interno es invertirla desde los
    productos publicados.

    Metodo
    ------
    1. Genera una malla regular de puntos sobre Chile continental.
    2. Cruza espacialmente cada punto con las capas publicadas TP, HC y PI del
       mismo dia de pronostico, obteniendo (clase de temperatura, clase de HCFM,
       decil de PI).
    3. Opcionalmente incorpora el sombreado, evaluando el hillshade del DEM en
       cada punto (funcion `dem_hillshade(lon, lat) -> 0..255`).
    4. Tabula la moda del decil de PI por combinacion.

    Acumulando varios dias se cubren las 288 combinaciones. El resultado queda
    a resolucion de decil; para afinarlo, complementar con la solicitud formal
    de la tabla al DEI/GEPRIF.

    Requiere geopandas y shapely.
    """
    import geopandas as gpd
    import numpy as np
    from shapely.geometry import shape

    xmin, ymin, xmax, ymax = extension
    lons = np.arange(xmin, xmax, paso_grados)
    lats = np.arange(ymin, ymax, paso_grados)
    malla = np.array([(x, y) for x in lons for y in lats])
    puntos = gpd.GeoDataFrame(
        {"lon": malla[:, 0], "lat": malla[:, 1]},
        geometry=gpd.points_from_xy(malla[:, 0], malla[:, 1]),
        crs="EPSG:4326")

    for servicio, columna in (("TP", "clase_tp"), ("HC", "clase_hc"), ("PI", "decil_pi")):
        features = consultar(servicio, dia, campos="label,date,var",
                             geometria=True, formato="geojson")
        capa = gpd.GeoDataFrame(
            [{"valor": f["properties"].get("label"),
              "fecha": f["properties"].get("date"),
              "geometry": shape(f["geometry"])} for f in features],
            crs="EPSG:4326")
        puntos = gpd.sjoin(puntos, capa[["valor", "geometry"]],
                           how="left", predicate="within")
        puntos = puntos.rename(columns={"valor": columna}).drop(columns=["index_right"])

    if dem_hillshade is not None:
        puntos["hillshade"] = [dem_hillshade(x, y)
                               for x, y in zip(puntos["lon"], puntos["lat"])]
        puntos["sombreado"] = (puntos["hillshade"] <= 123.5).map({True: 200, False: 100})
    else:
        puntos["sombreado"] = pd.NA

    puntos = puntos.dropna(subset=["clase_tp", "clase_hc", "decil_pi"])
    tabla = (puntos.groupby(["clase_hc", "clase_tp", "sombreado"], dropna=False)["decil_pi"]
                   .agg(decil_moda=lambda s: s.mode().iat[0] if len(s.mode()) else None,
                        decil_min="min", decil_max="max", n="size")
                   .reset_index())
    return tabla.sort_values(["clase_hc", "clase_tp"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Interfaz de linea de comandos
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Cliente de los servicios Boton Rojo de CONAF")
    ap.add_argument("accion", choices=["capas", "br", "resumen", "cosechar", "calibrar"])
    ap.add_argument("--servicio", default="PI")
    ap.add_argument("--dia", type=int, default=0)
    ap.add_argument("--salida", default=None)
    args = ap.parse_args()

    if args.accion == "capas":
        resultado = listar_capas(args.servicio)
    elif args.accion == "br":
        resultado = descargar_boton_rojo()
    elif args.accion == "resumen":
        resultado = resumen_comunal()
    elif args.accion == "cosechar":
        resultado = pd.DataFrame({"archivo": cosechar(servicios=(SERVICIO_BR,) + SERVICIOS_MET)})
    else:
        resultado = calibrar_matriz(dia=args.dia)

    if args.salida:
        (resultado.to_excel if args.salida.endswith(".xlsx") else resultado.to_csv)(
            args.salida, index=False)
        print(f"Escrito: {args.salida}  ({len(resultado)} filas)")
    else:
        print(resultado.to_string(max_rows=60))
