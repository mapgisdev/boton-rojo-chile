"""
tests/unit/test_dataset_qa_h3.py — Pruebas unitarias de integridad de datos QA y celdas territoriales H3 (Fase 2).
"""

from __future__ import annotations

from pathlib import Path
import unittest

import h3
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DERIVED_DIR = ROOT / "data" / "derived"
INCENDIOS_PARQUET = DERIVED_DIR / "incendios_qa.parquet"
INDEX_PARQUET = DERIVED_DIR / "h3_chile_r8_index.parquet"
WEIGHTS_PARQUET = DERIVED_DIR / "h3_commune_weights.parquet"


class TestDatasetQAH3(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.df_inc = pd.read_parquet(INCENDIOS_PARQUET)
        cls.df_idx = pd.read_parquet(INDEX_PARQUET)
        cls.df_weights = pd.read_parquet(WEIGHTS_PARQUET)

    def test_row_counts_and_completeness(self) -> None:
        """Verifica que el dataset procesado preserve exactamente las 68.546 filas del original."""
        self.assertEqual(len(self.df_inc), 68546)
        self.assertEqual(self.df_inc["event_id"].nunique(), 68546)
        self.assertEqual(len(self.df_idx), 33237)
        self.assertEqual(len(self.df_weights), 33237)

    def test_split_integrity(self) -> None:
        """Verifica la asignación estricta de particiones Train (71%), Val (10%) y Test Ciego (19%)."""
        self.assertEqual(self.df_inc["split"].isna().sum(), 0)
        split_counts = self.df_inc["split"].value_counts().to_dict()
        self.assertEqual(split_counts.get("train", 0), 48659)
        self.assertEqual(split_counts.get("validation", 0), 6947)
        self.assertEqual(split_counts.get("test", 0), 12940)

    def test_coordinate_qa_and_typo_fixes(self) -> None:
        """Verifica la corrección de erratas de coordenadas documentadas y asignación de flags."""
        # 1. Parral (index 9386)
        row_parral = self.df_inc[self.df_inc["event_id"] == 9386].iloc[0]
        self.assertEqual(row_parral["qa_coord_flag"], "QA_TYPO_CORRECTED")
        self.assertAlmostEqual(row_parral["lat"], -36.250000, places=4)
        self.assertIsNotNone(row_parral["h3_id"])

        # 2. Ercilla (index 25241)
        row_ercilla = self.df_inc[self.df_inc["event_id"] == 25241].iloc[0]
        self.assertEqual(row_ercilla["qa_coord_flag"], "QA_TYPO_CORRECTED")
        self.assertAlmostEqual(row_ercilla["lat"], -38.065556, places=4)
        self.assertIsNotNone(row_ercilla["h3_id"])

        # 3. Total de celdas H3 válidas
        valid_coords = self.df_inc[self.df_inc["qa_coord_flag"].isin(["QA_VALID", "QA_TYPO_CORRECTED"])]
        self.assertEqual(len(valid_coords), 68538)
        self.assertEqual(valid_coords["h3_id"].notna().sum(), 68538)

    def test_h3_cell_validity(self) -> None:
        """Verifica que todos los hexágonos H3 resolución 8 sean celdas válidas de Uber H3."""
        sample_cells = self.df_idx["h3_id"].sample(n=1000, random_state=42)
        for cell in sample_cells:
            self.assertTrue(h3.is_valid_cell(cell), f"Celda H3 inválida: {cell}")
            self.assertEqual(h3.get_resolution(cell), 8)

    def test_target_invariants(self) -> None:
        """Verifica los invariantes lógicos de superficie quemada y targets de grandes incendios."""
        self.assertTrue((self.df_inc["y_gt10ha"] == (self.df_inc["final_area_ha"] > 10.0).astype(int)).all())
        self.assertTrue((self.df_inc["y_gt50ha"] == (self.df_inc["final_area_ha"] > 50.0).astype(int)).all())
        self.assertTrue((self.df_inc["y_gt100ha"] == (self.df_inc["final_area_ha"] > 100.0).astype(int)).all())
        self.assertTrue((self.df_inc["y_gt1000ha"] == (self.df_inc["final_area_ha"] > 1000.0).astype(int)).all())

    def test_br_window_flag(self) -> None:
        """Verifica que la bandera in_br_window sea consistente con la hora de inicio local."""
        for _, row in self.df_inc.sample(n=500, random_state=42).iterrows():
            hr = row["hour_local"]
            if hr is not None:
                expected_in_window = (14 <= hr <= 18)
                self.assertEqual(row["in_br_window"], expected_in_window)


if __name__ == "__main__":
    unittest.main()
