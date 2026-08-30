"""
tests/unit/test_api_endpoints.py — Pruebas unitarias y de integración de endpoints REST de la API BR-HR (Fase 9).
"""

from __future__ import annotations

import unittest
from fastapi.testclient import TestClient

from src.api.main import app


class TestAPIEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_root_endpoint(self) -> None:
        """Verifica que el endpoint raíz responda 200 con la aplicación web o bienvenida."""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.text) > 0)

    def test_health_endpoint(self) -> None:
        """Verifica que /health retorne el estado del servicio y el conteo de celdas H3."""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["version"], "1.0.0")
        self.assertGreater(data["total_h3_cells"], 30000)
        self.assertGreater(data["total_communes"], 300)

    def test_forecast_summary(self) -> None:
        """Verifica el resumen nacional de alertas."""
        resp = self.client.get("/api/v1/forecast/latest/summary")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("date", data)
        self.assertIn("alert_counts", data)
        self.assertIn("rojo", data["alert_counts"])
        self.assertIn("amarillo", data["alert_counts"])
        self.assertIn("top_critical_communes", data)

    def test_communes_list_and_filters(self) -> None:
        """Verifica el listado de comunas y filtrado por región."""
        resp = self.client.get("/api/v1/forecast/latest/communes")
        self.assertEqual(resp.status_code, 200)
        communes = resp.json()
        self.assertGreater(len(communes), 300)

        first_com = communes[0]
        self.assertIn("comuna", first_com)
        self.assertIn("pct_superficie_roja", first_com)
        self.assertIn("alerta_comunal", first_com)

        # Filtrar por región
        resp_biobio = self.client.get("/api/v1/forecast/latest/communes?region=Biobío")
        self.assertEqual(resp_biobio.status_code, 200)
        self.assertGreater(len(resp_biobio.json()), 0)

    def test_commune_detail_and_404(self) -> None:
        """Verifica el endpoint de detalle de comuna y el manejo de 404 para comunas inexistentes."""
        # Comuna existente (por ejemplo Valparaíso o Concepción)
        resp_list = self.client.get("/api/v1/forecast/latest/communes")
        some_commune = resp_list.json()[0]["comuna"]

        resp_detail = self.client.get(f"/api/v1/forecast/latest/commune/{some_commune}")
        self.assertEqual(resp_detail.status_code, 200)
        detail = resp_detail.json()
        self.assertEqual(detail["comuna"].lower(), some_commune.lower())

        # Comuna inexistente
        resp_404 = self.client.get("/api/v1/forecast/latest/commune/ComunaInexistente999")
        self.assertEqual(resp_404.status_code, 404)

    def test_h3_cell_forecast_and_404(self) -> None:
        """Verifica la consulta de un hexágono H3 específico."""
        # Obtener un H3 id válido del resumen
        summary = self.client.get("/health").json()
        self.assertGreater(summary["total_h3_cells"], 0)

        # Consultar un hexágono conocido (ejemplo de Chile central)
        from src.api.services import forecast_service
        valid_id = forecast_service._h3_cache["h3_id"].iloc[0]

        resp_cell = self.client.get(f"/api/v1/forecast/latest/h3/{valid_id}")
        self.assertEqual(resp_cell.status_code, 200)
        cell_data = resp_cell.json()
        self.assertEqual(cell_data["h3_id"], valid_id)
        self.assertIn("p_ignicion", cell_data)
        self.assertIn("alerta", cell_data)

        # Hexágono inválido
        resp_invalid = self.client.get("/api/v1/forecast/latest/h3/invalid_h3_id_123")
        self.assertEqual(resp_invalid.status_code, 404)

    def test_trigger_forecast_endpoint(self) -> None:
        """Verifica el endpoint de disparo de inferencia."""
        resp = self.client.post("/api/v1/forecast/trigger", json={"use_live_gee": False})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertGreater(data["processed_cells"], 30000)


if __name__ == "__main__":
    unittest.main()
