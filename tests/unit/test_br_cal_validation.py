"""
tests/unit/test_br_cal_validation.py — Pruebas unitarias de verificación y ganancia estadística del modelo M1 (BR-CAL).
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_M1 = ROOT / "artifacts" / "m1_br_cal"
MATRIZ_FILE = ARTIFACTS_M1 / "matriz_pi_calibrada.json"
MODEL_CARD_FILE = ARTIFACTS_M1 / "model_card_m1.json"


class TestBRCalValidation(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(MATRIZ_FILE.exists(), f"Falta {MATRIZ_FILE}")
        self.assertTrue(MODEL_CARD_FILE.exists(), f"Falta {MODEL_CARD_FILE}")

        with open(MATRIZ_FILE, "r", encoding="utf-8") as f:
            self.matriz = {int(k): float(v) for k, v in json.load(f).items()}

        with open(MODEL_CARD_FILE, "r", encoding="utf-8") as f:
            self.model_card = json.load(f)

    def test_matrix_structure_and_bounds(self) -> None:
        """Verifica que la matriz M1 tenga 288 celdas y que todos sus valores estén en [0, 100] %."""
        self.assertEqual(len(self.matriz), 288)
        for clave, valor in self.matriz.items():
            self.assertGreaterEqual(valor, 0.0, f"Clave {clave} tiene valor negativo: {valor}")
            self.assertLessEqual(valor, 100.0, f"Clave {clave} supera 100 %: {valor}")

    def test_m1_statistical_gain_over_m0(self) -> None:
        """Verifica que M1 demuestre ganancia estadística cuantitativa frente a M0 en validación."""
        comp = self.model_card["comparison"]
        m0_metrics = self.model_card["metrics_validation_m0"]
        m1_metrics = self.model_card["metrics_validation_m1"]

        # Ganancia en detección POD
        self.assertGreater(comp["pod_gain"], 0.15, "M1 debe mejorar el POD en al menos 15 pp")
        # Ganancia en CSI
        self.assertGreater(comp["csi_gain"], 0.01, "M1 debe mejorar el CSI en validación")
        # Ganancia en F1
        self.assertGreater(comp["f1_gain"], 0.02, "M1 debe mejorar el F1 score en validación")
        # Mejora en calibración Brier Score
        self.assertLess(m1_metrics["brier_score"], m0_metrics["brier_score"], "M1 debe reducir el Brier Score")

    def test_blind_test_not_used(self) -> None:
        """Verifica que las métricas de model card solo correspondan a Train y Validation."""
        self.assertIn("train_samples", self.model_card)
        self.assertIn("validation_samples", self.model_card)
        self.assertNotIn("test_samples", self.model_card)


if __name__ == "__main__":
    unittest.main()
