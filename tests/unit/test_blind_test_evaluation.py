"""
tests/unit/test_blind_test_evaluation.py — Pruebas unitarias de verificación y certificación del test ciego 2022–2024.
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
BLIND_RESULTS_FILE = ROOT / "artifacts" / "evaluation" / "blind_test_results.json"


class TestBlindTestEvaluation(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(BLIND_RESULTS_FILE.exists(), f"Falta {BLIND_RESULTS_FILE}")
        with open(BLIND_RESULTS_FILE, "r", encoding="utf-8") as f:
            self.results = json.load(f)

    def test_blind_test_summary_counts(self) -> None:
        """Verifica que el test ciego contenga las dos temporadas (2022-23 y 2023-24) con >100.000 muestras."""
        summary = self.results["test_dataset_summary"]
        self.assertEqual(summary["total_samples"], 103512)
        self.assertEqual(summary["historical_fires"], 12939)
        self.assertIn("2022 al 2023", summary["seasons"])
        self.assertIn("2023 al 2024", summary["seasons"])

    def test_m1_superiority_over_m0_in_blind_test(self) -> None:
        """Verifica que M1 supere a M0 en POD y CSI sobre el test ciego no visto."""
        m0 = self.results["m0_baseline"]
        m1 = self.results["m1_recalibrated"]

        self.assertGreater(m1["pod"], m0["pod"] + 0.20, "M1 debe superar a M0 en más de 20 pp de detección en test ciego")
        self.assertGreater(m1["csi"], m0["csi"], "M1 debe superar a M0 en CSI")
        self.assertLess(m1["brier_score"], m0["brier_score"], "M1 debe tener menor error de Brier que M0")

    def test_m2_false_alarm_reduction_in_blind_test(self) -> None:
        """Verifica que M2 reduzca significativamente la tasa de falsas alarmas (FAR)."""
        m0 = self.results["m0_baseline"]
        m2 = self.results["m2_champion_p_ign"]

        self.assertLess(m2["far"], m0["far"] - 0.10, "M2 debe reducir el FAR en al menos 10 pp")
        self.assertGreater(m2["csi"], m0["csi"], "M2 debe superar el CSI de M0")
        self.assertGreater(m2["f1"], m0["f1"], "M2 debe superar el F1 score de M0")

    def test_m3_large_fire_discrimination_in_blind_test(self) -> None:
        """Verifica que los modelos M3 de grandes incendios alcancen ROC-AUC > 0.60 sobre los incendios reales de test ciego."""
        m3 = self.results["m3_large_fire_potential"]
        self.assertGreater(m3["p_gt10ha"]["roc_auc"], 0.60)
        self.assertGreater(m3["p_gt100ha"]["roc_auc"], 0.60)
        self.assertLess(m3["p_gt10ha"]["ece"], 0.05)
        self.assertLess(m3["p_gt100ha"]["ece"], 0.05)


if __name__ == "__main__":
    unittest.main()
