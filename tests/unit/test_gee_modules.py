"""
tests/unit/test_gee_modules.py — Pruebas unitarias de integración de módulos Google Earth Engine y pipelines H3 (Fase 7).
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest

import pandas as pd

from src.gee.gee_inference_pipeline import GEEInferenceEngine

ROOT = Path(__file__).resolve().parents[2]
GEE_DIR = ROOT / "src" / "gee"
DERIVED_DIR = ROOT / "data" / "derived"
FORECASTS_DIR = DERIVED_DIR / "forecasts"


class TestGEEModules(unittest.TestCase):
    def test_js_modules_content(self) -> None:
        """Verifica que los scripts JS de GEE contengan los 288 códigos y parámetros de Hillshade 313/60."""
        cal_js = GEE_DIR / "calibrated_module.js"
        app_js = GEE_DIR / "boton_rojo_hr_app.js"

        self.assertTrue(cal_js.exists(), f"Falta {cal_js}")
        self.assertTrue(app_js.exists(), f"Falta {app_js}")

        content_cal = cal_js.read_text(encoding="utf-8")
        self.assertIn("313.0", content_cal, "Hillshade debe usar acimut 313°")
        self.assertIn("60.0", content_cal, "Hillshade debe usar altitud 60°")
        self.assertIn("2101", content_cal)
        self.assertIn("17209", content_cal)

    def test_h3_geojson_structure(self) -> None:
        """Verifica que la malla GeoJSON H3 contenga exactamente 33.237 hexágonos válidos."""
        geojson_path = DERIVED_DIR / "h3_chile_r8_mesh.geojson"
        self.assertTrue(geojson_path.exists(), f"Falta {geojson_path}")

        with open(geojson_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["type"], "FeatureCollection")
        self.assertEqual(len(data["features"]), 33237)
        first_feat = data["features"][0]
        self.assertEqual(first_feat["geometry"]["type"], "Polygon")
        self.assertIn("h3_id", first_feat["properties"])
        # Un hexágono GeoJSON cerrado tiene 7 vértices
        self.assertEqual(len(first_feat["geometry"]["coordinates"][0]), 7)

    def test_inference_engine_execution(self) -> None:
        """Verifica que el motor de inferencia genere predicciones válidas para los 33.237 hexágonos."""
        engine = GEEInferenceEngine(use_live_gee=False)
        df_h3, df_communes = engine.run_daily_inference()

        self.assertEqual(len(df_h3), 33237)
        self.assertGreater(len(df_communes), 300)

        # Invariantes de predicciones
        self.assertTrue((df_h3["horas_boton_rojo"] >= 0).all())
        self.assertTrue((df_h3["horas_boton_rojo"] <= 5).all())
        self.assertTrue((df_h3["p_ignicion"] >= 0.0).all())
        self.assertTrue((df_h3["p_ignicion"] <= 1.0).all())
        self.assertTrue(df_h3["alerta"].isin(["VERDE", "TEMPRANA_PREVENTIVA", "AMARILLO", "ROJO"]).all())

        # Archivos exportados
        self.assertTrue((FORECASTS_DIR / "br_hr_h3_latest.parquet").exists())
        self.assertTrue((FORECASTS_DIR / "br_hr_communes_latest.json").exists())


if __name__ == "__main__":
    unittest.main()
