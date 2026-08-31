# -*- coding: utf-8 -*-
"""
pipeline.py — Replica ejecutable del Boton Rojo fuera de Google Earth Engine.

Cadena completa, auditable paso a paso y sin dependencia de servicios propietarios:

    1. Descarga del pronostico GFS 0,25 de NOAA (NOMADS, recorte a Chile)
    2. Seleccion de la ventana 14:00-18:59 hora local, dias d0 a d4
    3. HCFM, viento, clave compuesta y probabilidad de ignicion
    4. Regla de activacion y conteo de horas por pixel
    5. Mascara de superficie combustible
    6. Estadistica zonal por comuna -> tabla identica en estructura a la que
       publica CONAF (date, com_id, horas, SUM_br_ha, com_ha, proportion)

Insumos que debe proveer el usuario (una sola vez, como GeoTIFF en EPSG:4326):

    dem.tif          Modelo de elevacion. SRTM 90 m (CGIAR) o Copernicus DEM 30 m.
    worldcover.tif   ESA WorldCover v200 (2021), 10 m, con los codigos originales.
    comunas.gpkg     Division Politica Administrativa 2023 (SUBDERE/IGM/INE).

Dependencias:
    pip install requests numpy pandas xarray cfgrib eccodes rasterio geopandas shapely

Uso:
    python pipeline.py --salida boton_rojo_replica.xlsx
    python pipeline.py --fecha 2026-02-06 --sin-descarga --grib ./gfs
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import requests

from nucleo import (CLASES_COMBUSTIBLE, DIAS_PRONOSTICO, HORA_FIN, HORA_INICIO,
                    MATRIZ_PI, UMBRAL_PI, UMBRAL_VIENTO_KMH, clave_pi,
                    condicion_boton_rojo, hcfm, hillshade, reclass_g, viento_kmh)

# Chile continental. Ajustar si se requiere Isla de Pascua o territorio antartico.
EXTENSION = dict(oeste=-76.0, este=-66.0, sur=-56.0, norte=-17.0)
NOMADS = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl"
VARIABLES_GFS = ["TMP", "RH", "UGRD", "VGRD"]
NIVELES_GFS = {"lev_2_m_above_ground": "on", "lev_10_m_above_ground": "on"}


# ---------------------------------------------------------------------------
# 1. Descarga del pronostico
# ---------------------------------------------------------------------------

def desfase_utc_chile(momento: datetime) -> int:
    """-3 en horario de verano (primer sabado de septiembre a primer sabado de
    abril), -4 en horario normal. Chile continental."""
    anio = momento.year

    def primer_sabado(mes: int) -> datetime:
        d = datetime(anio, mes, 1, tzinfo=timezone.utc)
        return d + timedelta(days=(5 - d.weekday()) % 7)

    return -3 if (momento >= primer_sabado(9) or momento < primer_sabado(4)) else -4


def ultima_corrida_gfs(ahora: datetime = None) -> datetime:
    """Ciclo GFS mas reciente con disponibilidad razonable (latencia ~4,5 h)."""
    ahora = ahora or datetime.now(timezone.utc)
    referencia = ahora - timedelta(hours=5)
    ciclo = (referencia.hour // 6) * 6
    return referencia.replace(hour=ciclo, minute=0, second=0, microsecond=0)


def horas_pronostico_requeridas(corrida: datetime, dias: int = DIAS_PRONOSTICO) -> List[int]:
    """Horas de pronostico que caen en la ventana 14:00-18:59 local de d0..d(n-1)."""
    desfase = desfase_utc_chile(corrida)
    inicio_local = corrida + timedelta(hours=desfase)
    dia0 = inicio_local.date()
    requeridas = []
    for h in range(0, 121):
        valido_local = inicio_local + timedelta(hours=h)
        delta_dias = (valido_local.date() - dia0).days
        if 0 <= delta_dias < dias and HORA_INICIO <= valido_local.hour <= HORA_FIN:
            requeridas.append(h)
    return requeridas


def descargar_gfs(corrida: datetime, horas: List[int], destino: str = "gfs") -> List[str]:
    """Descarga los GRIB2 recortados a Chile desde el filtro NOMADS."""
    os.makedirs(destino, exist_ok=True)
    rutas = []
    for h in horas:
        nombre = f"gfs.t{corrida:%H}z.pgrb2.0p25.f{h:03d}"
        ruta = os.path.join(destino, f"{corrida:%Y%m%d}_{nombre}.grib2")
        if not os.path.exists(ruta) or os.path.getsize(ruta) == 0:
            params = {
                "file": nombre,
                "dir": f"/gfs.{corrida:%Y%m%d}/{corrida:%H}/atmos",
                "subregion": "",
                "leftlon": EXTENSION["oeste"], "rightlon": EXTENSION["este"],
                "toplat": EXTENSION["norte"], "bottomlat": EXTENSION["sur"],
            }
            params.update({f"var_{v}": "on" for v in VARIABLES_GFS})
            params.update(NIVELES_GFS)
            r = requests.get(NOMADS, params=params, timeout=180)
            r.raise_for_status()
            with open(ruta, "wb") as fh:
                fh.write(r.content)
        rutas.append(ruta)
    return rutas


def leer_gfs(rutas: List[str], desfase: int) -> "xr.Dataset":
    """Apila los GRIB en un Dataset con dimension `tiempo_local`."""
    import xarray as xr

    capas = []
    for ruta in rutas:
        superficie = xr.open_dataset(
            ruta, engine="cfgrib",
            backend_kwargs={"filter_by_keys": {"typeOfLevel": "heightAboveGround",
                                               "level": 2}})
        viento = xr.open_dataset(
            ruta, engine="cfgrib",
            backend_kwargs={"filter_by_keys": {"typeOfLevel": "heightAboveGround",
                                               "level": 10}})
        ds = xr.merge([superficie[["t2m", "r2"]], viento[["u10", "v10"]]],
                      compat="override")
        valido = pd.to_datetime(ds.valid_time.values) + pd.Timedelta(hours=desfase)
        capas.append(ds.expand_dims(tiempo_local=[valido]))
    combinado = xr.concat(capas, dim="tiempo_local").sortby("tiempo_local")
    combinado["t2m"] = combinado["t2m"] - 273.15          # K -> C
    combinado = combinado.assign_coords(
        longitude=(((combinado.longitude + 180) % 360) - 180)).sortby("longitude")
    return combinado


# ---------------------------------------------------------------------------
# 2. Rejilla de calculo y capas estaticas
# ---------------------------------------------------------------------------

def rejilla(paso_m: int = 2000) -> Tuple[np.ndarray, np.ndarray, dict]:
    """Malla regular en EPSG:4326 con paso aproximado equivalente a `paso_m`.

    CONAF publica sus poligonos sobre celdas de 4.000.000 m2 en EPSG:3857, es
    decir 2 km nominales. Se replica ese paso.
    """
    grados = paso_m / 111320.0
    lons = np.arange(EXTENSION["oeste"], EXTENSION["este"], grados)
    lats = np.arange(EXTENSION["norte"], EXTENSION["sur"], -grados)
    perfil = {"paso_grados": grados, "paso_m": paso_m,
              "ancho": len(lons), "alto": len(lats)}
    return lons, lats, perfil


def remuestrear(datos, lon_origen, lat_origen, lons, lats):
    """Interpolacion bilineal de la rejilla GFS a la rejilla de calculo."""
    from scipy.interpolate import RegularGridInterpolator

    orden_lat = np.argsort(lat_origen)
    interp = RegularGridInterpolator(
        (lat_origen[orden_lat], lon_origen), np.asarray(datos)[orden_lat, :],
        bounds_error=False, fill_value=None)
    malla_lat, malla_lon = np.meshgrid(lats, lons, indexing="ij")
    return interp(np.stack([malla_lat.ravel(), malla_lon.ravel()], axis=-1)
                  ).reshape(malla_lat.shape)


def leer_raster_estatico(ruta: str, lons: np.ndarray, lats: np.ndarray,
                         metodo: str = "nearest") -> np.ndarray:
    """Lee un GeoTIFF y lo remuestrea a la rejilla de calculo."""
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.warp import reproject

    destino = np.zeros((len(lats), len(lons)), dtype="float32")
    transformacion = rasterio.transform.from_origin(
        lons[0], lats[0], lons[1] - lons[0], lats[0] - lats[1])
    with rasterio.open(ruta) as src:
        reproject(source=rasterio.band(src, 1), destination=destino,
                  dst_transform=transformacion, dst_crs="EPSG:4326",
                  resampling=Resampling[metodo])
    return destino


# ---------------------------------------------------------------------------
# 3. Nucleo del indice
# ---------------------------------------------------------------------------

def calcular_horas_br(ds, lons, lats, hs_reclass, matriz=None) -> Dict[str, np.ndarray]:
    """Numero de horas en condicion de Boton Rojo por pixel, para cada dia local."""
    matriz = MATRIZ_PI if matriz is None else matriz
    tabla = np.full(max(matriz) + 1, np.nan)
    for k, v in matriz.items():
        tabla[k] = v

    lon_gfs = ds.longitude.values
    lat_gfs = ds.latitude.values
    por_dia: Dict[str, np.ndarray] = {}

    for tiempo in pd.to_datetime(ds.tiempo_local.values):
        corte = ds.sel(tiempo_local=tiempo)
        t = remuestrear(corte["t2m"].values, lon_gfs, lat_gfs, lons, lats)
        hr = np.clip(remuestrear(corte["r2"].values, lon_gfs, lat_gfs, lons, lats), 1, 100)
        u = remuestrear(corte["u10"].values, lon_gfs, lat_gfs, lons, lats)
        v = remuestrear(corte["v10"].values, lon_gfs, lat_gfs, lons, lats)

        m = hcfm(hr, t)
        claves = clave_pi(m, t, np.where(hs_reclass == 200, 0.0, 255.0))
        pi = np.where(claves > 0, tabla[np.clip(claves, 0, tabla.size - 1)], np.nan)
        condicion = condicion_boton_rojo(np.nan_to_num(pi), viento_kmh(u, v))

        clave_dia = tiempo.strftime("%Y-%m-%d")
        por_dia.setdefault(clave_dia, np.zeros(condicion.shape, dtype=np.int16))
        por_dia[clave_dia] += condicion.astype(np.int16)

    return por_dia


# ---------------------------------------------------------------------------
# 4. Estadistica zonal comunal
# ---------------------------------------------------------------------------

def estadistica_comunal(por_dia, lons, lats, mascara_combustible,
                        ruta_comunas: str, campo_id: str = "COMUNA",
                        campo_nombre: str = "NOM_COMUNA") -> pd.DataFrame:
    """Superficie en condicion de Boton Rojo por comuna, dia y numero de horas."""
    import geopandas as gpd
    import rasterio
    from rasterio.features import rasterize

    comunas = gpd.read_file(ruta_comunas).to_crs("EPSG:4326")
    transformacion = rasterio.transform.from_origin(
        lons[0], lats[0], lons[1] - lons[0], lats[0] - lats[1])
    forma = (len(lats), len(lons))

    indices = {i: fid for i, fid in enumerate(comunas[campo_id], start=1)}
    raster_comunas = rasterize(
        ((geom, i) for i, geom in enumerate(comunas.geometry, start=1)),
        out_shape=forma, transform=transformacion, fill=0, dtype="int32")

    # Superficie de celda en hectareas, corregida por latitud.
    paso = lons[1] - lons[0]
    alto_m = paso * 111320.0
    ancho_m = paso * 111320.0 * np.cos(np.deg2rad(lats))[:, None]
    area_ha = np.broadcast_to(alto_m * ancho_m / 10000.0, forma)

    combustible = mascara_combustible.astype(bool)
    filas = []
    superficie_combustible = {}
    for i, fid in indices.items():
        en_comuna = raster_comunas == i
        superficie_combustible[fid] = float(area_ha[en_comuna & combustible].sum())

    for fecha, horas in sorted(por_dia.items()):
        for h in range(1, DIAS_PRONOSTICO + 1):
            objetivo = (horas == h) & combustible
            if not objetivo.any():
                continue
            for i, fid in indices.items():
                seleccion = objetivo & (raster_comunas == i)
                if not seleccion.any():
                    continue
                ha = float(area_ha[seleccion].sum())
                com_ha = superficie_combustible[fid] or np.nan
                filas.append({
                    "date": fecha,
                    "com_id": fid,
                    "com": comunas.loc[comunas[campo_id] == fid, campo_nombre].iat[0],
                    "horas": h,
                    "SUM_br_ha": round(ha, 2),
                    "com_ha": round(com_ha, 2),
                    "proportion": round(ha / com_ha, 4) if com_ha else np.nan,
                })
    return pd.DataFrame(filas).sort_values(["date", "com_id", "horas"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# 5. Orquestacion
# ---------------------------------------------------------------------------

def ejecutar(args) -> pd.DataFrame:
    corrida = (datetime.strptime(args.corrida, "%Y%m%d%H").replace(tzinfo=timezone.utc)
               if args.corrida else ultima_corrida_gfs())
    desfase = desfase_utc_chile(corrida)
    horas = horas_pronostico_requeridas(corrida)
    print(f"Corrida GFS   : {corrida:%Y-%m-%d %H}Z   (Chile = UTC{desfase:+d})")
    print(f"Pasos horarios: {len(horas)} -> {horas[:6]}{' ...' if len(horas) > 6 else ''}")

    rutas = ([os.path.join(args.grib, f) for f in sorted(os.listdir(args.grib))]
             if args.sin_descarga else descargar_gfs(corrida, horas, args.grib))
    ds = leer_gfs(rutas, desfase)

    lons, lats, perfil = rejilla(args.paso)
    print(f"Rejilla       : {perfil['ancho']} x {perfil['alto']} celdas de {args.paso} m")

    dem = leer_raster_estatico(args.dem, lons, lats, "bilinear")
    hs = reclass_g(hillshade(dem, args.paso))
    cobertura = leer_raster_estatico(args.worldcover, lons, lats, "mode")
    combustible = np.isin(np.rint(cobertura).astype(int), CLASES_COMBUSTIBLE)
    print(f"Combustible   : {100 * combustible.mean():.1f} % de la rejilla")

    por_dia = calcular_horas_br(ds, lons, lats, hs)
    for fecha, horas_br in sorted(por_dia.items()):
        activas = int(((horas_br > 0) & combustible).sum())
        print(f"  {fecha}: {activas:>7,} celdas combustibles en condicion de Boton Rojo"
              .replace(",", "."))

    tabla = estadistica_comunal(por_dia, lons, lats, combustible, args.comunas,
                                args.campo_id, args.campo_nombre)
    print(f"Resultado     : {len(tabla)} filas, "
          f"{tabla['com_id'].nunique()} comunas activadas")
    return tabla


def main():
    ap = argparse.ArgumentParser(description="Replica del Boton Rojo de CONAF")
    ap.add_argument("--corrida", help="Ciclo GFS AAAAMMDDHH. Por defecto, el ultimo.")
    ap.add_argument("--grib", default="gfs", help="Carpeta de archivos GRIB2")
    ap.add_argument("--sin-descarga", action="store_true",
                    help="Usar los GRIB ya presentes en --grib")
    ap.add_argument("--dem", default="dem.tif")
    ap.add_argument("--worldcover", default="worldcover.tif")
    ap.add_argument("--comunas", default="comunas.gpkg")
    ap.add_argument("--campo-id", default="COMUNA")
    ap.add_argument("--campo-nombre", default="NOM_COMUNA")
    ap.add_argument("--paso", type=int, default=2000, help="Paso de la rejilla, en m")
    ap.add_argument("--paso-zonal", type=int, default=500,
                    help="Paso de la contabilidad de superficie, en m. CONAF usa 500: "
                         "todos los valores publicados de com_ha son multiplos de 25 ha")
    ap.add_argument("--salida", default="boton_rojo_replica.xlsx")
    args = ap.parse_args()

    tabla = ejecutar(args)
    if args.salida.endswith(".xlsx"):
        tabla.to_excel(args.salida, index=False)
    else:
        tabla.to_csv(args.salida, index=False)
    print(f"Escrito: {args.salida}")


if __name__ == "__main__":
    main()
