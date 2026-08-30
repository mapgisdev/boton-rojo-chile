"""
src/shared/export_r2_pmtiles.py — Exportador de artefactos estáticos y publicador en Cloudflare R2.

Genera los archivos optimizados para distribución CDN en Cloudflare R2 / Pages:
- Malla territorial H3 (GeoJSON comprimido / PMTiles)
- Límites Comunales de Chile
- Tablas de pronóstico JSON / Parquet de celdas H3 y comunas
- Opcionalmente sube a un bucket Cloudflare R2 mediante la API S3 compatible de boto3.
"""

from __future__ import annotations

import gzip
import json
import os
from pathlib import Path
import shutil
from typing import Any, Dict, Optional

import boto3
from botocore.config import Config
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DERIVED_DIR = DATA_DIR / "derived"
FORECASTS_DIR = DERIVED_DIR / "forecasts"
R2_EXPORT_DIR = DATA_DIR / "r2_export"


def prepare_r2_artifacts(output_dir: Path = R2_EXPORT_DIR) -> Dict[str, Path]:
    """Genera y empaqueta todos los artefactos estáticos requeridos para la distribución global."""
    output_dir.mkdir(parents=True, exist_ok=True)
    generated: Dict[str, Path] = {}

    print(f"Preparando artefactos para Cloudflare R2 en: {output_dir}")

    # 1. Copiar y Comprimir Malla H3 (GeoJSON)
    mesh_source = DERIVED_DIR / "h3_chile_r8_mesh.geojson"
    if not mesh_source.exists():
        from src.gee.h3_hex_geojson_generator import generate_h3_geojson
        generate_h3_geojson(output_geojson=mesh_source)

    target_mesh = output_dir / "h3_chile_r8_mesh.geojson"
    shutil.copyfile(mesh_source, target_mesh)
    generated["mesh_geojson"] = target_mesh

    # Versión comprimida gzip para descarga ultrarrápida (< 1.8 MB)
    target_mesh_gz = output_dir / "h3_chile_r8_mesh.geojson.gz"
    with open(mesh_source, "rb") as f_in, gzip.open(target_mesh_gz, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    generated["mesh_geojson_gz"] = target_mesh_gz
    print(f"[OK] Malla H3 comprimida: {target_mesh_gz.stat().st_size / (1024*1024):.2f} MB")

    # 2. Copiar Límites Comunales de Chile
    comunas_source = DERIVED_DIR / "comunas_chile_gee_asset.geojson"
    if not comunas_source.exists():
        from src.gee.prepare_comunas_asset import prepare_comunas_asset
        prepare_comunas_asset()

    target_comunas = output_dir / "comunas_chile.geojson"
    shutil.copyfile(comunas_source, target_comunas)
    generated["comunas_geojson"] = target_comunas
    print(f"[OK] Límites comunales: {target_comunas.stat().st_size / (1024*1024):.2f} MB")

    # 3. Exportar Datos del Último Pronóstico
    h3_parquet = FORECASTS_DIR / "br_hr_h3_latest.parquet"
    com_json = FORECASTS_DIR / "br_hr_communes_latest.json"

    if not h3_parquet.exists():
        from src.gee.gee_inference_pipeline import GEEInferenceEngine
        engine = GEEInferenceEngine(use_live_gee=False)
        engine.run_daily_inference()

    # Copiar resumen de comunas
    target_com_json = output_dir / "br_hr_communes_latest.json"
    shutil.copyfile(com_json, target_com_json)
    generated["communes_json"] = target_com_json

    # Exportar H3 en JSON optimizado
    df_h3 = pd.read_parquet(h3_parquet)
    target_h3_json = output_dir / "br_hr_h3_latest.json"
    # Exportar solo columnas esenciales para ahorrar ancho de banda
    essential_cols = ["h3_id", "horas_boton_rojo", "p_ignicion", "p_gran_incendio", "alerta"]
    cols_to_use = [c for c in essential_cols if c in df_h3.columns]
    df_h3[cols_to_use].to_json(target_h3_json, orient="records", indent=None)
    generated["h3_json"] = target_h3_json

    # Generar Resumen Nacional
    counts = df_h3["alerta"].value_counts().to_dict()
    total_cells = len(df_h3)
    rojo_count = int(counts.get("ROJO", 0))
    summary_data = {
        "service": "BR-HR — Botón Rojo de Alta Resolución",
        "date": str(df_h3["date"].iloc[0]) if "date" in df_h3.columns else "2026-08-30",
        "total_cells": total_cells,
        "alert_counts": {
            "verde": int(counts.get("VERDE", 0)),
            "temprana_preventiva": int(counts.get("TEMPRANA_PREVENTIVA", 0)),
            "amarillo": int(counts.get("AMARILLO", 0)),
            "rojo": rojo_count,
        },
        "pct_territorio_rojo": round((rojo_count / total_cells) * 100.0, 2) if total_cells > 0 else 0.0,
    }

    target_summary = output_dir / "br_hr_summary_latest.json"
    with open(target_summary, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    generated["summary_json"] = target_summary

    # 4. Copiar Muestra de Incendios Históricos para el Visualizador
    incendios_asset_csv = DERIVED_DIR / "incendios_historicos_conaf_asset.csv"
    if incendios_asset_csv.exists():
        df_inc = pd.read_csv(incendios_asset_csv)
        # Tomar los incendios más relevantes (>10 ha o megaincendios) para visualización fluida
        df_top_fires = df_inc.sort_values(by="area_ha", ascending=False).head(5000)
        target_fires = output_dir / "incendios_historicos_top.json"
        fires_list = []
        for _, row in df_top_fires.iterrows():
            fires_list.append({
                "date": str(row.get("date", "")),
                "lat": round(float(row.get("lat", 0)), 4),
                "lon": round(float(row.get("lon", 0)), 4),
                "area_ha": round(float(row.get("area_ha", 0)), 1),
                "comuna": str(row.get("comuna", "")),
                "region": str(row.get("region", "")),
            })
        with open(target_fires, "w", encoding="utf-8") as f:
            json.dump(fires_list, f, ensure_ascii=False)
        generated["fires_json"] = target_fires
        print(f"[OK] Incendios historicos exportados: {len(fires_list):,} eventos ({target_fires.stat().st_size / 1024:.1f} KB)")

    print("Artefactos de Cloudflare R2 generados exitosamente.")
    return generated


def upload_to_cloudflare_r2(
    local_dir: Path = R2_EXPORT_DIR,
    bucket_name: Optional[str] = None,
    account_id: Optional[str] = None,
    access_key: Optional[str] = None,
    secret_key: Optional[str] = None,
) -> bool:
    """Sube los archivos generados a Cloudflare R2 usando la API S3 de boto3."""
    account_id = account_id or os.environ.get("R2_ACCOUNT_ID")
    access_key = access_key or os.environ.get("R2_ACCESS_KEY_ID")
    secret_key = secret_key or os.environ.get("R2_SECRET_ACCESS_KEY")
    bucket_name = bucket_name or os.environ.get("R2_BUCKET_NAME", "boton-rojo-chile")

    if not all([account_id, access_key, secret_key]):
        print("Variables de Cloudflare R2 no configuradas. Guardando archivos localmente en 'data/r2_export/'.")
        return False

    endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
    print(f"Conectando con Cloudflare R2: {endpoint_url} (Bucket: {bucket_name})...")

    s3_client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )

    for file_path in local_dir.glob("*"):
        if file_path.is_file():
            key = f"br_hr/{file_path.name}"
            content_type = "application/json" if file_path.suffix == ".json" else "application/octet-stream"
            if file_path.name.endswith(".geojson"):
                content_type = "application/geo+json"

            print(f"Subiendo {file_path.name} -> {key}...")
            s3_client.upload_file(
                str(file_path),
                bucket_name,
                key,
                ExtraArgs={
                    "ContentType": content_type,
                    "CacheControl": "public, max-age=3600",
                },
            )

    print("Todos los artefactos fueron subidos a Cloudflare R2 con éxito.")
    return True


if __name__ == "__main__":
    prepare_r2_artifacts()
