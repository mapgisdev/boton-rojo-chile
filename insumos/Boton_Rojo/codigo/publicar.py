# -*- coding: utf-8 -*-
"""
publicar.py — Publicación del Botón Rojo con la pila abierta.

Toma lo que dejó el cálculo y lo convierte en tres cosas publicables:

    1. COG (Cloud Optimized GeoTIFF) por variable, día y hora, que TiTiler tesela
       al vuelo sin pregenerar pirámides.
    2. Ítems STAC en pgstac, para que "el mapa de probabilidad de ignición del
       día D" sea una consulta y no una convención de nombres de archivo.
    3. Una tabla en PostGIS con las comunas activadas, que Martin sirve como
       teselas vectoriales y pygeoapi como OGC API - Features.

Equivalencias con la pila propietaria:

    Export.image.toAsset / Feature Service   ->  COG + TiTiler
    Colección de Earth Engine                ->  Colección STAC en pgstac
    Dashboard de ArcGIS                      ->  Panel o Grafana sobre PostGIS
    (no existía)                             ->  pygeoapi: OGC API Features y Coverages

Dependencias:
    pip install rio-cogeo pystac pypgstac[psycopg] psycopg[binary] geopandas

Uso:
    python -m botonrojo.publicar --productos /datos/productos --cog /datos/cog
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import date, datetime, timezone
from typing import Dict, Iterable, List

COLECCION = "boton-rojo"

# Metadatos de cada variable publicada. Las rampas replican la simbología con
# que CONAF publica hoy, de modo que los mapas propios y los oficiales sean
# comparables a simple vista.
VARIABLES: Dict[str, Dict] = {
    "TP": {"titulo": "Temperatura", "unidad": "°C", "rampa": "rdylbu_r", "rango": (-5, 40)},
    "HR": {"titulo": "Humedad relativa", "unidad": "%", "rampa": "blues", "rango": (0, 100)},
    "VV": {"titulo": "Velocidad del viento", "unidad": "km/h", "rampa": "ylorrd", "rango": (0, 40)},
    "HC": {"titulo": "Humedad del combustible fino muerto", "unidad": "%", "rampa": "rdylgn", "rango": (0, 30)},
    "PI": {"titulo": "Probabilidad de ignición", "unidad": "%", "rampa": "turbo", "rango": (0, 100)},
    "BR": {"titulo": "Horas en condición de Botón Rojo", "unidad": "h", "rampa": "ylorrd", "rango": (0, 5)},
}

# d0_20260826_PI.tif
PATRON = re.compile(r"^d(?P<dia>\d)_(?P<fecha>\d{8})_(?P<var>[A-Z]{2})\.tif$", re.I)


# ---------------------------------------------------------------------------
# 1. COG
# ---------------------------------------------------------------------------

def a_cog(origen: str, destino: str, sobrescribir: bool = False) -> str:
    """Convierte un GeoTIFF en COG con compresión DEFLATE y vistas generales."""
    from rio_cogeo.cogeo import cog_translate
    from rio_cogeo.profiles import cog_profiles

    if os.path.exists(destino) and not sobrescribir:
        return destino
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    perfil = cog_profiles.get("deflate")
    perfil.update(BLOCKSIZE=512, PREDICTOR=2, ZLEVEL=9)
    cog_translate(origen, destino, perfil, overview_resampling="average",
                  web_optimized=False, quiet=True)
    return destino


# ---------------------------------------------------------------------------
# 2. STAC
# ---------------------------------------------------------------------------

def coleccion_stac() -> Dict:
    """Definición de la colección. Se carga una sola vez."""
    import pystac

    col = pystac.Collection(
        id=COLECCION,
        description=(
            "Índice diario de peligro de incendios forestales tipo Botón Rojo: "
            "probabilidad de ignición, humedad del combustible fino muerto y las "
            "variables meteorológicas de las que derivan, sobre superficie "
            "combustible. Pronóstico a cinco días para la ventana 14:00-18:59."),
        extent=pystac.Extent(
            spatial=pystac.SpatialExtent([[-75.7, -56.0, -66.4, -17.5]]),
            temporal=pystac.TemporalExtent([[datetime(2026, 1, 1, tzinfo=timezone.utc), None]])),
        title="Botón Rojo — réplica UIA",
        license="proprietary",
        providers=[pystac.Provider(
            name="CONAF — Unidad de Información y Análisis",
            roles=[pystac.ProviderRole.PROCESSOR, pystac.ProviderRole.HOST])],
    )
    col.extra_fields["boton_rojo:umbral_pi"] = 70
    col.extra_fields["boton_rojo:umbral_viento_kmh"] = 20
    col.extra_fields["boton_rojo:ventana_horaria"] = "14:00-18:59 America/Santiago"
    return col.to_dict(include_self_link=False)


def item_stac(ruta_cog: str, variable: str, fecha: date, dia: int,
              url_base: str) -> Dict:
    """Construye el ítem STAC de un COG, con su extensión geográfica real."""
    import pystac
    import rasterio
    from rasterio.warp import transform_bounds

    with rasterio.open(ruta_cog) as src:
        limites = transform_bounds(src.crs, "EPSG:4326", *src.bounds, densify_pts=21)
        forma = [src.height, src.width]
        transformacion = list(src.transform)[:6]

    meta = VARIABLES[variable]
    item = pystac.Item(
        id=f"{fecha:%Y%m%d}_d{dia}_{variable}",
        geometry={"type": "Polygon", "coordinates": [[
            [limites[0], limites[1]], [limites[2], limites[1]],
            [limites[2], limites[3]], [limites[0], limites[3]],
            [limites[0], limites[1]]]]},
        bbox=list(limites),
        datetime=datetime(fecha.year, fecha.month, fecha.day, 17, 0, tzinfo=timezone.utc),
        collection=COLECCION,
        properties={
            "boton_rojo:variable": variable,
            "boton_rojo:dia_pronostico": dia,
            "boton_rojo:unidad": meta["unidad"],
            "title": f"{meta['titulo']} — {fecha:%d-%m-%Y} (d{dia})",
            "proj:shape": forma,
            "proj:transform": transformacion,
        })
    item.add_asset("data", pystac.Asset(
        href=f"{url_base.rstrip('/')}/{os.path.basename(ruta_cog)}",
        media_type=pystac.MediaType.COG,
        roles=["data"],
        title=meta["titulo"]))
    return item.to_dict(include_self_link=False)


def cargar_en_pgstac(coleccion: Dict, items: List[Dict], dsn: str) -> None:
    """Inserta o actualiza colección e ítems en pgstac (upsert idempotente)."""
    from pypgstac.db import PgstacDB
    from pypgstac.load import Loader, Methods

    with PgstacDB(dsn=dsn) as bd:
        cargador = Loader(db=bd)
        cargador.load_collections(iter([coleccion]), insert_mode=Methods.upsert)
        cargador.load_items(iter(items), insert_mode=Methods.upsert)


# ---------------------------------------------------------------------------
# 3. PostGIS: comunas activadas
# ---------------------------------------------------------------------------

DDL = """
CREATE TABLE IF NOT EXISTS boton_rojo_comuna (
    fecha        date        NOT NULL,
    com_id       integer     NOT NULL,
    comuna       text        NOT NULL,
    provincia    text,
    region       text,
    horas        smallint    NOT NULL CHECK (horas BETWEEN 1 AND 5),
    ha_activada  double precision NOT NULL,
    ha_combustible double precision,
    proporcion   double precision,
    corrida      timestamptz NOT NULL DEFAULT now(),
    geom         geometry(MultiPolygon, 4326),
    PRIMARY KEY (fecha, com_id, horas)
);
CREATE INDEX IF NOT EXISTS ix_br_fecha  ON boton_rojo_comuna (fecha DESC);
CREATE INDEX IF NOT EXISTS ix_br_region ON boton_rojo_comuna (region);
CREATE INDEX IF NOT EXISTS ix_br_geom   ON boton_rojo_comuna USING gist (geom);

-- Vista que consumen Martin (teselas vectoriales) y pygeoapi (OGC API Features):
-- una fila por comuna y día, con el máximo de horas alcanzado.
CREATE OR REPLACE VIEW boton_rojo_vigente AS
SELECT fecha, com_id, comuna, provincia, region,
       max(horas)             AS horas_max,
       sum(ha_activada)       AS ha_activada,
       max(ha_combustible)    AS ha_combustible,
       sum(ha_activada) / nullif(max(ha_combustible), 0) AS proporcion,
       max(corrida)           AS corrida,
       (array_agg(geom))[1]   AS geom
FROM boton_rojo_comuna
WHERE fecha >= current_date
GROUP BY fecha, com_id, comuna, provincia, region;
"""


def cargar_comunas(csv_o_gpkg: str, dsn: str, capa_geom: str = None) -> int:
    """Carga la tabla comunal del día en PostGIS, reemplazando esas fechas."""
    import geopandas as gpd
    import pandas as pd
    import psycopg

    if csv_o_gpkg.endswith((".gpkg", ".geojson", ".shp")):
        df = gpd.read_file(csv_o_gpkg, layer=capa_geom).to_crs("EPSG:4326")
    else:
        df = pd.read_csv(csv_o_gpkg)

    renombres = {"date": "fecha", "com": "comuna", "prov": "provincia", "reg": "region",
                 "SUM_br_ha": "ha_activada", "com_ha": "ha_combustible",
                 "proportion": "proporcion"}
    df = df.rename(columns={k: v for k, v in renombres.items() if k in df.columns})
    columnas = ["fecha", "com_id", "comuna", "provincia", "region", "horas",
                "ha_activada", "ha_combustible", "proporcion"]
    df = df[[c for c in columnas if c in df.columns]]

    with psycopg.connect(dsn, autocommit=False) as cx:
        cx.execute(DDL)
        fechas = sorted({str(f) for f in df["fecha"]})
        cx.execute("DELETE FROM boton_rojo_comuna WHERE fecha = ANY(%s::date[])", (fechas,))
        with cx.cursor().copy(
                "COPY boton_rojo_comuna (" + ",".join(df.columns) + ") FROM STDIN") as copia:
            for fila in df.itertuples(index=False):
                copia.write_row(tuple(fila))
        cx.commit()
    return len(df)


# ---------------------------------------------------------------------------
# 4. Orquestación
# ---------------------------------------------------------------------------

def recorrer_productos(directorio: str) -> Iterable[Dict]:
    for nombre in sorted(os.listdir(directorio)):
        m = PATRON.match(nombre)
        if m and m.group("var").upper() in VARIABLES:
            yield {
                "ruta": os.path.join(directorio, nombre),
                "nombre": nombre,
                "dia": int(m.group("dia")),
                "fecha": datetime.strptime(m.group("fecha"), "%Y%m%d").date(),
                "var": m.group("var").upper(),
            }


def main():
    ap = argparse.ArgumentParser(description="Publicación del Botón Rojo")
    ap.add_argument("--productos", default="/datos/productos",
                    help="GeoTIFF dNN_AAAAMMDD_XX.tif que dejó el cálculo")
    ap.add_argument("--cog", default="/datos/cog", help="Destino de los COG")
    ap.add_argument("--comunas", default=None,
                    help="CSV o GPKG con la tabla comunal del día")
    ap.add_argument("--dsn", default=os.environ.get(
        "BR_DSN", "postgresql://botonrojo@localhost:5432/botonrojo"))
    ap.add_argument("--url-base", default=os.environ.get(
        "BR_URL_COG", "file:///datos/cog"),
        help="Prefijo con que TiTiler alcanza los COG")
    ap.add_argument("--sin-stac", action="store_true")
    args = ap.parse_args()

    items, convertidos = [], 0
    for producto in recorrer_productos(args.productos):
        destino = os.path.join(args.cog, f"{producto['fecha']:%Y%m}", producto["nombre"])
        a_cog(producto["ruta"], destino)
        convertidos += 1
        if not args.sin_stac:
            items.append(item_stac(destino, producto["var"], producto["fecha"],
                                   producto["dia"], args.url_base))

    print(f"COG generados            : {convertidos}")

    if items:
        cargar_en_pgstac(coleccion_stac(), items, args.dsn)
        print(f"Ítems STAC actualizados  : {len(items)}")

    if args.comunas:
        n = cargar_comunas(args.comunas, args.dsn)
        print(f"Filas comunales cargadas : {n}")

    print("\nComprobación rápida:")
    print("  curl -s localhost:8081/collections/boton-rojo/items?limit=3 | jq '.features[].id'")
    print("  curl -s 'localhost:8082/cog/info?url=/datos/cog/…/d0_AAAAMMDD_PI.tif' | jq .band_metadata")
    print("  curl -s localhost:8083/collections/boton_rojo_vigente/items?limit=3 | jq '.numberMatched'")


if __name__ == "__main__":
    main()
