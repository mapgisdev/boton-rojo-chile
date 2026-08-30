"""
src/api/services.py — Capa de lógica de negocio, caché en memoria y orquestación de datos de BR-HR.
"""

from __future__ import annotations

from datetime import date, datetime
import json
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.gee.gee_inference_pipeline import GEEInferenceEngine

ROOT = Path(__file__).resolve().parents[2]
DERIVED_DIR = ROOT / "data" / "derived"
FORECASTS_DIR = DERIVED_DIR / "forecasts"
H3_INDEX_PATH = DERIVED_DIR / "h3_chile_r8_index.parquet"
COMMUNE_WEIGHTS_PATH = DERIVED_DIR / "h3_commune_weights.parquet"
GEOJSON_MESH_PATH = DERIVED_DIR / "h3_chile_r8_mesh.geojson"


class ForecastService:
    """Servicio de gestión de pronósticos, índices H3 y agregaciones comunales."""

    def __init__(self) -> None:
        self._h3_cache: Optional[pd.DataFrame] = None
        self._communes_cache: Optional[List[Dict[str, Any]]] = None
        self._last_loaded_mtime: float = 0.0
        self._h3_index_df: Optional[pd.DataFrame] = None
        self._geojson_cache: Optional[Dict[str, Any]] = None

        self._load_h3_index()
        self._reload_forecast_if_needed()

    def _load_h3_index(self) -> None:
        if H3_INDEX_PATH.exists():
            self._h3_index_df = pd.read_parquet(H3_INDEX_PATH)
            # Asegurar indexación rápida por h3_id
            if "h3_id" in self._h3_index_df.columns:
                self._h3_index_df.set_index("h3_id", inplace=True, drop=False)

    def _reload_forecast_if_needed(self) -> None:
        parquet_file = FORECASTS_DIR / "br_hr_h3_latest.parquet"
        communes_file = FORECASTS_DIR / "br_hr_communes_latest.json"

        if not parquet_file.exists():
            # Si no existe, ejecutar inferencia inicial
            engine = GEEInferenceEngine(use_live_gee=False)
            df_h3, df_com = engine.run_daily_inference()
            self._h3_cache = df_h3
            self._communes_cache = df_com.to_dict(orient="records")
            return

        mtime = parquet_file.stat().st_mtime
        if self._h3_cache is None or mtime > self._last_loaded_mtime:
            self._h3_cache = pd.read_parquet(parquet_file)
            if communes_file.exists():
                with open(communes_file, "r", encoding="utf-8") as f:
                    self._communes_cache = json.load(f)
            self._last_loaded_mtime = mtime

    def is_gee_connected(self) -> bool:
        """Verifica si Google Earth Engine está autenticado."""
        try:
            import ee
            if ee.data._credentials is not None or bool(os.environ.get("GEE_SERVICE_ACCOUNT_JSON")):
                return True
            # Buscar archivo en insumos
            insumos = ROOT / "insumos"
            return bool(list(insumos.glob("*.json")))
        except Exception:
            return False

    def get_health(self) -> Dict[str, Any]:
        self._reload_forecast_if_needed()
        latest_date = None
        if self._h3_cache is not None and not self._h3_cache.empty and "date" in self._h3_cache.columns:
            latest_date = str(self._h3_cache["date"].iloc[0])

        total_cells = len(self._h3_cache) if self._h3_cache is not None else 0
        total_communes = len(self._communes_cache) if self._communes_cache is not None else 0

        return {
            "status": "ok",
            "version": "1.0.0",
            "gee_connected": self.is_gee_connected(),
            "latest_forecast_date": latest_date,
            "total_h3_cells": total_cells,
            "total_communes": total_communes,
        }

    def get_summary(self) -> Dict[str, Any]:
        self._reload_forecast_if_needed()
        if self._h3_cache is None or self._h3_cache.empty:
            raise ValueError("No hay pronóstico cargado.")

        df = self._h3_cache
        total_cells = len(df)
        counts = df["alerta"].value_counts().to_dict()

        verde = int(counts.get("VERDE", 0))
        temp = int(counts.get("TEMPRANA_PREVENTIVA", 0))
        amarillo = int(counts.get("AMARILLO", 0))
        rojo = int(counts.get("ROJO", 0))

        red_pct = round((rojo / total_cells) * 100.0, 2) if total_cells > 0 else 0.0

        # Top comunas críticas
        top_communes = []
        if self._communes_cache:
            sorted_com = sorted(self._communes_cache, key=lambda x: x.get("pct_superficie_roja", 0), reverse=True)
            top_communes = sorted_com[:10]

        return {
            "date": str(df["date"].iloc[0]),
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total_cells": total_cells,
            "alert_counts": {
                "verde": verde,
                "temprana_preventiva": temp,
                "amarillo": amarillo,
                "rojo": rojo,
            },
            "red_alert_percentage": red_pct,
            "top_critical_communes": top_communes,
        }

    def get_communes(self, region: Optional[str] = None, alert_level: Optional[str] = None) -> List[Dict[str, Any]]:
        self._reload_forecast_if_needed()
        if not self._communes_cache:
            return []

        res = self._communes_cache
        if region:
            res = [c for c in res if region.lower() in c.get("region", "").lower()]
        if alert_level:
            res = [c for c in res if c.get("alerta_comunal", "").upper() == alert_level.upper()]

        return res

    def get_commune_detail(self, comuna_name: str) -> Optional[Dict[str, Any]]:
        self._reload_forecast_if_needed()
        if not self._communes_cache:
            return None

        com_match = next((c for c in self._communes_cache if c.get("comuna", "").lower() == comuna_name.lower()), None)
        if not com_match:
            return None

        # Obtener celdas H3 de la comuna si existen en la tabla de ponderaciones
        associated_cells = []
        if COMMUNE_WEIGHTS_PATH.exists() and self._h3_cache is not None:
            weights_df = pd.read_parquet(COMMUNE_WEIGHTS_PATH)
            com_cells = weights_df[weights_df["comuna"].str.lower() == comuna_name.lower()]
            if not com_cells.empty:
                cell_ids = com_cells["h3_id"].tolist()
                sub_h3 = self._h3_cache[self._h3_cache["h3_id"].isin(cell_ids)]
                associated_cells = sub_h3.to_dict(orient="records")

        detail = dict(com_match)
        detail["cells"] = associated_cells
        return detail

    def get_h3_cell(self, h3_id: str) -> Optional[Dict[str, Any]]:
        self._reload_forecast_if_needed()
        if self._h3_cache is None or self._h3_cache.empty:
            return None

        cell_rows = self._h3_cache[self._h3_cache["h3_id"] == h3_id]
        if cell_rows.empty:
            return None

        row = cell_rows.iloc[0].to_dict()

        # Enriquecer con comuna principal si está en el índice
        if self._h3_index_df is not None and h3_id in self._h3_index_df.index:
            idx_row = self._h3_index_df.loc[h3_id]
            row["comuna_principal"] = str(idx_row.get("comuna", ""))
            row["region"] = str(idx_row.get("region", ""))

        return row

    def get_h3_geojson(self) -> Dict[str, Any]:
        """Devuelve la malla territorial GeoJSON con los valores de riesgo inyectados."""
        self._reload_forecast_if_needed()
        if self._geojson_cache is not None:
            return self._geojson_cache

        if not GEOJSON_MESH_PATH.exists():
            from src.gee.h3_hex_geojson_generator import generate_h3_geojson
            generate_h3_geojson(output_geojson=GEOJSON_MESH_PATH)

        with open(GEOJSON_MESH_PATH, "r", encoding="utf-8") as f:
            geojson = json.load(f)

        # Inyectar propiedades de riesgo en cada feature
        if self._h3_cache is not None:
            h3_dict = self._h3_cache.set_index("h3_id").to_dict(orient="index")
            for feat in geojson.get("features", []):
                h_id = feat.get("properties", {}).get("h3_id")
                if h_id in h3_dict:
                    val = h3_dict[h_id]
                    feat["properties"]["horas_br"] = int(val.get("horas_boton_rojo", 0))
                    feat["properties"]["p_ign"] = float(val.get("p_ignicion", 0.0))
                    feat["properties"]["p_gf"] = float(val.get("p_gran_incendio", 0.0))
                    feat["properties"]["alerta"] = str(val.get("alerta", "VERDE"))

        self._geojson_cache = geojson
        return geojson

    def trigger_forecast(self, target_date: Optional[str] = None, use_live_gee: bool = True) -> Dict[str, Any]:
        """Ejecuta el cómputo de inferencia diario y actualiza la caché."""
        t0 = time.time()
        d = date.fromisoformat(target_date) if target_date else date.today()

        engine = GEEInferenceEngine(use_live_gee=use_live_gee)
        df_h3, df_communes = engine.run_daily_inference(target_date=d)

        self._h3_cache = df_h3
        self._communes_cache = df_communes.to_dict(orient="records")
        self._geojson_cache = None  # Invalidar caché geojson
        self._last_loaded_mtime = time.time()

        elapsed = round(time.time() - t0, 2)
        return {
            "status": "success",
            "target_date": d.isoformat(),
            "processed_cells": len(df_h3),
            "processed_communes": len(df_communes),
            "elapsed_seconds": elapsed,
        }


# Instancia singleton del servicio
forecast_service = ForecastService()
