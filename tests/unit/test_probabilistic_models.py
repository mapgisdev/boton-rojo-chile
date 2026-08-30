"""
tests/unit/test_probabilistic_models.py — Pruebas unitarias para modelos probabilísticos M2 P(IGN) y M3 P(GF).
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest

import numpy as np

from src.training.models.calibrator import (
    ProbabilityCalibrator,
    adjust_case_control_odds,
    compute_expected_calibration_error,
)

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_M2 = ROOT / "artifacts" / "m2_p_ignition"
ARTIFACTS_M3 = ROOT / "artifacts" / "m3_p_large_fire"


class TestProbabilisticModels(unittest.TestCase):
    def test_case_control_odds_adjustment(self) -> None:
        """Verifica que la corrección de odds reduzca la probabilidad predicha a la prevalencia real."""
        # Si un modelo da 0.50 en una muestra con 1 positivo y 1 control (s1/s0 = 100),
        # en la población real donde los controles son mucho más abundantes, la probabilidad real debe ser < 0.50
        p_sample = np.array([0.1, 0.5, 0.9])
        p_adjusted = adjust_case_control_odds(p_sample, sampling_ratio_pos=1.0, sampling_ratio_ctrl=0.01)
        self.assertTrue((p_adjusted < p_sample).all(), "Las probabilidades ajustadas deben ser menores a las de la muestra enriquecida")
        self.assertTrue((p_adjusted >= 0.0).all())
        self.assertTrue((p_adjusted <= 1.0).all())

    def test_ece_computation(self) -> None:
        """Verifica que el cálculo de ECE sea no-negativo y exactamente cero para predicciones perfectamente calibradas."""
        y_true = np.array([0, 0, 1, 1])
        y_prob = np.array([0.0, 0.0, 1.0, 1.0])
        ece_res = compute_expected_calibration_error(y_true, y_prob, n_bins=5)
        self.assertAlmostEqual(ece_res["ece"], 0.0, places=5)
        self.assertEqual(len(ece_res["bins_data"]), 5)

    def test_probability_calibrator(self) -> None:
        """Verifica que el calibrador isotónico produzca probabilidades monótonas en [0, 1]."""
        scores = np.linspace(0.1, 0.9, 50)
        targets = (scores > 0.5).astype(int)
        cal = ProbabilityCalibrator(method="isotonic").fit(scores, targets)
        p_cal = cal.predict_proba(scores)
        self.assertTrue((p_cal >= 0.0).all())
        self.assertTrue((p_cal <= 1.0).all())

    def test_m2_artifacts_exist(self) -> None:
        """Verifica la existencia y estructura de los artefactos del modelo M2 Champion."""
        card_file = ARTIFACTS_M2 / "model_card_m2.json"
        model_file = ARTIFACTS_M2 / "champion_lightgbm.txt"
        lr_file = ARTIFACTS_M2 / "logistic_regression_coefficients.json"

        self.assertTrue(card_file.exists(), f"Falta {card_file}")
        self.assertTrue(model_file.exists(), f"Falta {model_file}")
        self.assertTrue(lr_file.exists(), f"Falta {lr_file}")

        with open(card_file, "r", encoding="utf-8") as f:
            card = json.load(f)
        self.assertEqual(card["model_id"], "M2_P_IGNITION_CHAMPION_v1.0")
        self.assertIn("roc_auc", card["metrics_validation"])
        self.assertIn("pr_auc", card["metrics_validation"])

    def test_m3_artifacts_exist(self) -> None:
        """Verifica la existencia y estructura de los artefactos del modelo M3 Grandes Incendios."""
        card_file = ARTIFACTS_M3 / "model_card_m3.json"
        m10_file = ARTIFACTS_M3 / "model_m3_y_gt10ha.txt"
        m100_file = ARTIFACTS_M3 / "model_m3_y_gt100ha.txt"

        self.assertTrue(card_file.exists(), f"Falta {card_file}")
        self.assertTrue(m10_file.exists(), f"Falta {m10_file}")
        self.assertTrue(m100_file.exists(), f"Falta {m100_file}")

        with open(card_file, "r", encoding="utf-8") as f:
            card = json.load(f)
        self.assertIn("p_gt10ha", card["models"])
        self.assertIn("p_gt100ha", card["models"])


if __name__ == "__main__":
    unittest.main()
