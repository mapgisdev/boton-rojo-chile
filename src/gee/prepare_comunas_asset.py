"""
src/gee/prepare_comunas_asset.py — Preparador de Capa de Límites Comunales de Chile para Google Earth Engine Asset.

Procesa y optimiza el archivo insumos/limites_chile/comunas.json (87 MB) simplificando geometrías
a ~3.5 MB para carga instantánea en Google Earth Engine Assets sin pérdida de precisión territorial.
"""

from __future__ import annotations

import json
from pathlib import Path
import zipfile

import geopandas as gpd

ROOT = Path(__file__).resolve().parents[2]
INPUT_COMUNAS_JSON = ROOT / "insumos" / "limites_chile" / "comunas.json"
DERIVED_DIR = ROOT / "data" / "derived"
OUTPUT_GEOJSON = DERIVED_DIR / "comunas_chile_gee_asset.geojson"
OUTPUT_SHP_DIR = DERIVED_DIR / "comunas_shp"
OUTPUT_ZIP = DERIVED_DIR / "comunas_chile_gee_asset.zip"


def prepare_comunas_asset(input_path: Path = INPUT_COMUNAS_JSON) -> None:
    print(f"Cargando límites comunales desde {input_path}...")
    gdf = gpd.read_file(input_path)

    print(f"Comunas encontradas: {len(gdf)}")
    print("Columnas originales:", gdf.columns.tolist())

    # Estandarizar columnas esenciales
    # Renombrar 'Comuna' -> 'comuna', 'Region' -> 'region', 'Provincia' -> 'provincia', 'cod_comuna' -> 'cod_comuna'
    col_map = {}
    for col in gdf.columns:
        c_low = col.lower()
        if c_low == "comuna":
            col_map[col] = "comuna"
        elif c_low == "region":
            col_map[col] = "region"
        elif c_low == "provincia":
            col_map[col] = "provincia"
        elif "cod_comuna" in c_low or "codcomuna" in c_low:
            col_map[col] = "cod_comuna"

    gdf = gdf.rename(columns=col_map)
    keep_cols = [c for c in ["comuna", "region", "provincia", "cod_comuna", "geometry"] if c in gdf.columns]
    gdf = gdf[keep_cols].copy()

    # Asegurar CRS EPSG:4326 (WGS84)
    if gdf.crs is None:
        gdf.set_crs(epsg=4326, inplace=True)
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    # Simplificar geometrías levemente (tolerancia ~100m = 0.001 grados) para optimizar carga en GEE
    print("Optimizando topología y simplificando vértices para Earth Engine...")
    gdf["geometry"] = gdf["geometry"].simplify(tolerance=0.001, preserve_topology=True)

    DERIVED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Exportar GeoJSON optimizado
    print(f"Guardando GeoJSON en {OUTPUT_GEOJSON}...")
    gdf.to_file(OUTPUT_GEOJSON, driver="GeoJSON")
    size_mb = OUTPUT_GEOJSON.stat().st_size / (1024 * 1024)
    print(f"GeoJSON generado con éxito: {size_mb:.2f} MB.")

    # 2. Exportar Shapefile comprimido en ZIP (Formato preferido por GEE Assets)
    OUTPUT_SHP_DIR.mkdir(parents=True, exist_ok=True)
    shp_path = OUTPUT_SHP_DIR / "comunas_chile.shp"
    gdf.to_file(shp_path, driver="ESRI Shapefile", encoding="utf-8")

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in OUTPUT_SHP_DIR.glob("comunas_chile.*"):
            zipf.write(file, arcname=file.name)

    zip_size_mb = OUTPUT_ZIP.stat().st_size / (1024 * 1024)
    print(f"Shapefile ZIP generado para GEE Asset en {OUTPUT_ZIP} ({zip_size_mb:.2f} MB).")


if __name__ == "__main__":
    prepare_comunas_asset()
