"""
tests/unit/test_leakage_invariants.py — Pruebas automáticas de invariantes anti-leakage y contratos de datos.
"""

from __future__ import annotations

from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from src.training.features.builder import calculate_vpd
from src.training.sampling.case_control import generate_case_control_samples

PROHIBITED_LEAKAGE_FEATURES = {
    "dt_deteccion", "dt_aviso", "dt_despacho", "dt_salida",
    "dt_arribo", "dt_primer_ataque", "dt_control", "dt_extincion",
    "duracion_horas", "causa_especifica", "predio", "propietario",
    "arribo_superficie_ha", "primer_ataque_superficie_ha", "control_superficie_ha"
}


class TestLeakageInvariants(unittest.TestCase):
    def test_vpd_calculation(self) -> None:
        """Verifica que el cálculo de VPD sea físicamente válido (no negativo y monótono con T)."""
        temp = np.array([20.0, 30.0, 40.0])
        rh = np.array([50.0, 50.0, 50.0])
        vpd = calculate_vpd(temp, rh)
        self.assertTrue((vpd >= 0).all())
        self.assertTrue(vpd[2] > vpd[1] > vpd[0], "VPD debe aumentar con la temperatura a HR constante")

    def test_controls_targets_are_zero(self) -> None:
        """Verifica que todos los controles tengan y_ignition=0 y targets de severidad=0."""
        # Generar una muestra pequeña para verificación rápida
        df_sample = generate_case_control_samples(n_spatial_controls=2, n_temporal_controls=1)
        controls = df_sample[df_sample["sample_type"].isin(["spatial_control", "temporal_control"])]
        
        self.assertTrue((controls["y_ignition"] == 0).all())
        self.assertTrue((controls["y_gt10ha"] == 0).all())
        self.assertTrue((controls["y_gt50ha"] == 0).all())
        self.assertTrue((controls["y_gt100ha"] == 0).all())
        self.assertTrue((controls["final_area_ha"] == 0.0).all())

    def test_sample_weights_positive(self) -> None:
        """Verifica que todos los registros tengan pesos de muestreo estrictamente positivos."""
        df_sample = generate_case_control_samples(n_spatial_controls=2, n_temporal_controls=1)
        self.assertTrue((df_sample["sample_weight"] > 0).all())
        self.assertTrue((df_sample["inclusion_probability"] > 0).all())
        self.assertTrue((df_sample["inclusion_probability"] <= 1.0).all())


if __name__ == "__main__":
    unittest.main()
