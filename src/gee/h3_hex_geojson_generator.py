"""
src/gee/h3_hex_geojson_generator.py — Generador de GeoJSON para Malla Hexagonal H3-8 en Google Earth Engine.

Convierte el registro maestro de celdas H3-8 en una FeatureCollection GeoJSON lista para importar
como Asset o FeatureCollection en GEE (`ee.FeatureCollection`).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import h3
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DERIVED_DIR = ROOT / "data" / "derived"
INDEX_PARQUET = DERIVED_DIR / "h3_chile_r8_index.parquet"
OUTPUT_GEOJSON = DERIVED_DIR / "h3_chile_r8_mesh.geojson"


def generate_h3_geojson(index_path: Path = INDEX_PARQUET,
                        out_path: Path = OUTPUT_GEOJSON,
                        sample_limit: Optional[int] = None) -> Dict[str, Any]:
    """Genera un archivo GeoJSON con los polígonos exactos de los hexágonos H3-8."""
    print(f"Cargando celdas H3 desde {index_path}...")
    df = pd.read_parquet(index_path)

    if sample_limit is not None and sample_limit < len(df):
        df = df.head(sample_limit)

    print(f"Construyendo geometrías de polígonos H3 para {len(df):,} hexágonos...")
    features = []

    for row in df.itertuples(index=False):
        cell_id = row.h3_id
        # En h3 v4 cell_to_boundary devuelve tuplas (lat, lon)
        boundary_coords = h3.cell_to_boundary(cell_id)
        # GeoJSON estándar requiere [lon, lat]
        geojson_ring = [[round(lon, 6), round(lat, 6)] for lat, lon in boundary_coords]
        # Cerrar el anillo lineal si no está cerrado
        if geojson_ring[0] != geojson_ring[-1]:
            geojson_ring.append(geojson_ring[0])

        feature = {
            "type": "Feature",
            "properties": {
                "h3_id": cell_id,
                "codcom": str(row.codcom),
                "comuna": str(row.comuna),
                "region": str(row.region),
                "provincia": str(row.provincia),
                "lat_center": round(float(row.lat_center), 6),
                "lon_center": round(float(row.lon_center), 6),
                "historical_fire_count": int(row.historical_fire_count),
                "historical_burned_ha": round(float(row.historical_burned_ha), 2),
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [geojson_ring],
            },
        }
        features.append(feature)

    fc = {
        "type": "FeatureCollection",
        "features": features,
    }

    print(f"Guardando GeoJSON en {out_path}...")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(fc, f)

    print(f"GeoJSON exportado con éxito: {len(features):,} hexágonos.")
    return fc


if __name__ == "__main__":
    generate_h3_geojson()
