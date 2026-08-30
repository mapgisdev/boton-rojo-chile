"""
tests/unit/test_baseline_golden.py — Pruebas unitarias de regresión estricta del baseline M0 (BR-CONAF).
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest

import numpy as np

from src.baseline.conaf_core import (
    acumulacion_horas_br,
    clave_compuesta,
    condicion_boton_rojo,
    hcfm,
    probabilidad_ignicion,
    reclass_a,
    reclass_c,
    reclass_g,
    viento_kmh,
)
from src.baseline.pi_matrix import MATRIZ_BASE_ROTHERMEL, pi_continua_rothermel
from src.baseline.tables import UMBRAL_PI, UMBRAL_VIENTO_KMH


class TestBaselineGolden(unittest.TestCase):
    def setUp(self) -> None:
        self.fixtures_path = Path(__file__).resolve().parents[1] / "fixtures" / "golden_samples.json"
        with open(self.fixtures_path, "r", encoding="utf-8") as f:
            self.fixtures = json.load(f)

    def test_golden_cases(self) -> None:
        """Verifica cada caso dorado contra los valores de referencia precomputados."""
        for case in self.fixtures["cases"]:
            name = case["name"]
            inp = case["inputs"]
            exp = case["expected"]

            # 1. HCFM
            val_hcfm = hcfm(inp["hr_pct"], inp["temp_c"])
            self.assertAlmostEqual(val_hcfm, exp["hcfm"], places=3, msg=f"HCFM fallo en {name}")

            # 2. Viento
            val_viento = viento_kmh(inp["u10"], inp["v10"])
            self.assertAlmostEqual(val_viento, exp["viento_kmh"], places=3, msg=f"Viento fallo en {name}")

            # 3. Reclasificaciones
            val_ra = reclass_a(inp["temp_c"])
            self.assertEqual(val_ra, exp["reclass_a"], msg=f"Reclass A fallo en {name}")

            val_rc = reclass_c(val_hcfm)
            self.assertEqual(val_rc, exp["reclass_c"], msg=f"Reclass C fallo en {name}")

            val_rg = reclass_g(inp["hs"])
            self.assertEqual(val_rg, exp["reclass_g"], msg=f"Reclass G fallo en {name}")

            # 4. Clave compuesta
            val_clave = clave_compuesta(val_hcfm, inp["temp_c"], inp["hs"])
            self.assertEqual(val_clave, exp["clave"], msg=f"Clave fallo en {name}")

            # 5. Probabilidad de ignición
            val_pi = probabilidad_ignicion(inp["temp_c"], inp["hr_pct"], inp["hs"])
            self.assertAlmostEqual(val_pi, exp["pi_pct"], places=1, msg=f"PI fallo en {name}")

            # 6. Activación Botón Rojo
            val_br = condicion_boton_rojo(val_pi, val_viento)
            self.assertEqual(val_br, exp["boton_rojo"], msg=f"Boton Rojo fallo en {name}")

    def test_matrix_dimensions(self) -> None:
        """Verifica que la matriz Rothermel contenga exactamente las 288 celdas esperadas."""
        self.assertEqual(len(MATRIZ_BASE_ROTHERMEL), 288)

    def test_nwcg_table_closeness(self) -> None:
        """Verifica que la ecuación Rothermel replique la tabla NWCG impreso con error < 1.0 pp."""
        # Tabla NWCG unshaded: T bulbo seco (F) vs HCFM (2..17)
        tabla_nwcg = {
            115: [100, 100, 80, 70, 60, 60, 50, 40, 40, 30, 30, 20, 20, 20, 20, 10],
            105: [100, 90, 80, 70, 60, 60, 50, 40, 40, 30, 30, 20, 20, 20, 10, 10],
            95:  [100, 90, 80, 70, 60, 50, 40, 40, 30, 30, 30, 20, 20, 20, 10, 10],
            85:  [100, 90, 80, 70, 60, 50, 40, 40, 30, 30, 20, 20, 20, 10, 10, 10],
            75:  [100, 80, 70, 60, 60, 50, 40, 40, 30, 30, 20, 20, 20, 10, 10, 10],
            65:  [90, 80, 70, 60, 50, 50, 40, 30, 30, 20, 20, 20, 20, 10, 10, 10],
            55:  [90, 80, 70, 60, 50, 40, 40, 30, 30, 20, 20, 20, 10, 10, 10, 10],
            45:  [90, 80, 70, 60, 50, 40, 40, 30, 30, 20, 20, 20, 10, 10, 10, 10],
            35:  [80, 70, 60, 50, 50, 40, 30, 30, 20, 20, 20, 10, 10, 10, 10, 10],
        }
        errores = []
        for tf, fila in tabla_nwcg.items():
            tc = (tf - 32.0) * 5.0 / 9.0
            for m, ref in zip(range(2, 18), fila):
                calc = round(float(pi_continua_rothermel(tc, m, 0.0)), -1)
                errores.append(abs(calc - ref))
        error_medio = sum(errores) / len(errores)
        self.assertLess(error_medio, 1.0, "El error medio respecto a la tabla NWCG debe ser < 1.0 pp")

    def test_hourly_accumulation(self) -> None:
        """Verifica la suma de horas activadas en la ventana 14-18."""
        # Shape: (5 horas, 2 pixeles)
        condiciones = np.array([
            [True, False],
            [True, True],
            [True, True],
            [False, True],
            [True, False]
        ])
        horas = acumulacion_horas_br(condiciones)
        np.testing.assert_array_equal(horas, np.array([4, 3]))


if __name__ == "__main__":
    unittest.main()
