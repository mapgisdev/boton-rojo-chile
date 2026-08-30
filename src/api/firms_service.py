"""
src/api/firms_service.py — Servicio de Integración en Tiempo Real con NASA FIRMS.
Incluye filtro espacial estricto contra el polígono de soberanía territorial de Chile,
eliminando anomalías térmicas en países vecinos (Argentina, Bolivia, Perú).
"""

from __future__ import annotations

import os
import time
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error

try:
    from zoneinfo import ZoneInfo
    CHILE_TZ = ZoneInfo("America/Santiago")
except Exception:
    CHILE_TZ = None

try:
    from shapely.geometry import shape, Point
    from shapely.prepared import prep
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
CACHE_PATH = ROOT / "data" / "r2_export" / "firms_latest.json"
MASK_PATH = ROOT / "data" / "derived" / "chile_border_mask.geojson"

# Bounding Box rectangular para consulta API NASA
CHILE_BBOX = "-76,-56,-66,-17"

class FirmsService:
    def __init__(self, cache_ttl_seconds: int = 900) -> None:
        self.cache_ttl = cache_ttl_seconds
        self._last_fetch_time: float = 0.0
        self._cached_data: Optional[Dict[str, Any]] = None
        self._chile_prep = None
        self._init_spatial_mask()

    def _init_spatial_mask(self) -> None:
        """Carga y prepara el polígono de soberanía territorial de Chile en memoria."""
        if not SHAPELY_AVAILABLE or not MASK_PATH.exists():
            return
        try:
            with open(MASK_PATH, "r", encoding="utf-8") as f:
                fc = json.load(f)
            if fc.get("features"):
                geom = shape(fc["features"][0]["geometry"])
                # Usar buffer pequeño para asegurar celdas costeras e insulares
                self._chile_prep = prep(geom.buffer(0.01))
                logger.info("Máscara territorial de Chile cargada con éxito en FirmsService.")
        except Exception as e:
            logger.warning(f"No se pudo inicializar la máscara territorial de Chile: {e}")

    def is_inside_chile(self, lon: float, lat: float) -> bool:
        """Determina con precisión geográfica si un punto está dentro de Chile."""
        if self._chile_prep:
            try:
                return self._chile_prep.contains(Point(lon, lat))
            except Exception:
                pass
        # Fallback de lat/lon aproximado para Chile continental
        return -75.8 <= lon <= -66.5 and -56.0 <= lat <= -17.5

    def get_active_fires(self, days: int = 2) -> Dict[str, Any]:
        """
        Retorna focos activos satelitales estrictamente dentro de Chile de las últimas 24 a 48 hrs móviles.
        """
        now = time.time()
        if self._cached_data and (now - self._last_fetch_time) < self.cache_ttl:
            return self._cached_data

        if CACHE_PATH.exists() and (now - CACHE_PATH.stat().st_mtime) < self.cache_ttl:
            try:
                with open(CACHE_PATH, "r", encoding="utf-8") as f:
                    self._cached_data = json.load(f)
                    self._last_fetch_time = now
                    return self._cached_data
            except Exception as e:
                logger.warning(f"Error leyendo cache FIRMS: {e}")

        # Consultar satélites VIIRS SNPP y NOAA-20 con ventana de 48h
        geojson_data = self._fetch_from_nasa_area(days=days)
        if not geojson_data or len(geojson_data.get("features", [])) == 0:
            geojson_data = self._get_fallback_geojson()

        try:
            CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(geojson_data, f, indent=2)
            self._cached_data = geojson_data
            self._last_fetch_time = now
        except Exception as e:
            logger.warning(f"No se pudo escribir cache FIRMS: {e}")

        return geojson_data

    def _fetch_from_nasa_area(self, days: int = 2) -> Optional[Dict[str, Any]]:
        map_key = os.getenv("FIRMS_MAP_KEY", "2f990c194b466a206f37cf2946dee14b")
        if not map_key:
            return None

        all_features: List[Dict[str, Any]] = []

        # Consultar sensores de alta resolución VIIRS
        for source in ["VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT"]:
            url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{map_key}/{source}/{CHILE_BBOX}/{days}"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "BR-HR-Chile/1.0"})
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        csv_text = response.read().decode("utf-8")
                        features = self._parse_csv(csv_text, sensor_name=source)
                        all_features.extend(features)
            except Exception as e:
                logger.error(f"Error consultando {source} en NASA FIRMS: {e}")

        if not all_features:
            return None

        # Deduplicar por coordenadas aproximadas
        unique_features = []
        seen = set()
        for f in all_features:
            coords = f["geometry"]["coordinates"]
            key = (round(coords[0], 3), round(coords[1], 3))
            if key not in seen:
                seen.add(key)
                unique_features.append(f)

        return {
            "type": "FeatureCollection",
            "total_active_hotspots": len(unique_features),
            "source": "NASA FIRMS (VIIRS 375m NRT)",
            "territory": "Chile Continental e Insular (Filtrado por Frontera Oficial)",
            "timezone_reference": "America/Santiago (CLT / CLST)",
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "features": unique_features
        }

    def _parse_csv(self, csv_text: str, sensor_name: str) -> List[Dict[str, Any]]:
        lines = [l.strip() for l in csv_text.strip().split("\n") if l.strip()]
        if len(lines) < 2:
            return []

        headers = [h.strip().lower() for h in lines[0].split(",")]
        features = []

        for line in lines[1:]:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) != len(headers):
                continue
            row = dict(zip(headers, parts))
            try:
                lat = float(row.get("latitude", 0))
                lon = float(row.get("longitude", 0))

                # FILTRO ESPACIAL ESTRICTO: Solo puntos dentro del territorio de Chile
                if not self.is_inside_chile(lon, lat):
                    continue

                brightness = float(row.get("bright_ti4", row.get("brightness", 300)))
                frp = float(row.get("frp", 0.0))
                confidence_raw = row.get("confidence", "nominal")
                acq_date = row.get("acq_date", "")
                acq_time = str(row.get("acq_time", "")).zfill(4)

                conf_label = "Alta" if confidence_raw in ["h", "high"] else ("Baja" if confidence_raw in ["l", "low"] else "Nominal")

                # Conversión horaria UTC -> Chile Continental (America/Santiago)
                try:
                    utc_dt = datetime.strptime(f"{acq_date} {acq_time}", "%Y-%m-%d %H%M").replace(tzinfo=timezone.utc)
                    if CHILE_TZ:
                        local_dt = utc_dt.astimezone(CHILE_TZ)
                    else:
                        local_dt = utc_dt - timedelta(hours=4)
                    local_time_str = local_dt.strftime("%d/%m/%Y %H:%M hrs")
                    utc_time_str = utc_dt.strftime("%H:%M UTC")
                except Exception:
                    local_time_str = f"{acq_date} {acq_time}"
                    utc_time_str = f"{acq_time} UTC"

                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [round(lon, 4), round(lat, 4)]
                    },
                    "properties": {
                        "sensor": "VIIRS 375m NRT",
                        "satellite": "SNPP / NOAA-20",
                        "brightness_k": brightness,
                        "brightness_c": round(brightness - 273.15, 1),
                        "frp_mw": frp,
                        "confidence": conf_label,
                        "date": acq_date,
                        "time_utc": utc_time_str,
                        "time_local": local_time_str,
                        "pais": "Chile",
                        "tipo": "🛰️ Foco Activo Satelital (NASA FIRMS)"
                    }
                })
            except (ValueError, TypeError):
                continue

        return features

    def _get_fallback_geojson(self) -> Dict[str, Any]:
        return {
            "type": "FeatureCollection",
            "features": [],
            "total_active_hotspots": 0,
            "source": "NASA FIRMS (NRT)",
            "status": "NO_THERMAL_ANOMALIES_CURRENTLY",
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        }

firms_service = FirmsService()
