# -*- coding: utf-8 -*-
"""
tests/unit/test_m0_golden_suite.py — Suite de pruebas doradas y casos de frontera para M0.
"""

from __future__ import annotations

import unittest
import numpy as np
import pandas as pd

from src.m0_original import (
    CLASES_COMBUSTIBLE,
    DIAS_PRONOSTICO,
    HORA_FIN,
    HORA_INICIO,
    M0_FROZEN,
    M0_VERSION,
    MATRIZ_PI_ROTHERMEL,
    UMBRAL_PI,
    UMBRAL_VIENTO_KMH,
    clave_pi,
    condicion_boton_rojo,
    construir_matriz_pi,
    hcfm,
    hillshade,
    horas_boton_rojo,
    mascara_combustible,
    pi_continua_rothermel,
    probabilidad_ignicion,
    reclass_a,
    reclass_b,
    reclass_c,
    reclass_d,
    reclass_e,
    reclass_f,
    reclass_g,
    reducir_comunal,
    viento_kmh,
)


class TestM0GoldenSuite(unittest.TestCase):
    def test_version_and_frozen_flag(self) -> None:
        """Verifica que M0 esté formalmente congelado en versión 1.0.0."""
        self.assertEqual(M0_VERSION, "1.0.0")
        self.assertTrue(M0_FROZEN)

    def test_hcfm_exact_formula(self) -> None:
        """Verifica la regresión de equilibrio HCFM de la U. de Chile en puntos críticos."""
        # 1. Caso estándar (HR=50 %, T=25 °C)
        val = hcfm(50.0, 25.0)
        exp = 0.297374 + 0.262 * 50.0 - 0.00982 * 25.0  # 13.151874 %
        self.assertAlmostEqual(val, exp, places=5)
        self.assertAlmostEqual(val, 13.151874, places=5)

        # 2. Caso extremo seco (HR=5 %, T=40 °C)
        val_seco = hcfm(5.0, 40.0)
        self.assertAlmostEqual(val_seco, 1.214574, places=5)

        # 3. Caso húmedo (HR=95 %, T=10 °C)
        val_humedo = hcfm(95.0, 10.0)
        self.assertAlmostEqual(val_humedo, 25.089174, places=5)

    def test_wind_euclidean_kmh(self) -> None:
        """Verifica el cálculo del viento en km/h a 10 m."""
        # 1. Calmo
        self.assertEqual(viento_kmh(0.0, 0.0), 0.0)

        # 2. Pitágoras exacto (3, 4 -> 5 m/s = 18.0 km/h)
        self.assertAlmostEqual(viento_kmh(3.0, 4.0), 18.0, places=5)

        # 3. Supera umbral de 20 km/h (u=4.0, v=4.0 -> ~20.36 km/h)
        v_critico = viento_kmh(4.0, 4.0)
        self.assertGreater(v_critico, 20.0)
        self.assertAlmostEqual(v_critico, np.sqrt(32.0) * 3.6, places=5)

    def test_reclass_boundaries_rigorous(self) -> None:
        """Verifica de forma exhaustiva los límites inclusivos/exclusivos de las 7 tablas."""
        # Reclass A: Cortes [0, 5, 10, 15, 20, 25, 30, 35, 40]
        self.assertEqual(reclass_a(-10.0), 1)
        self.assertEqual(reclass_a(0.0), 1)
        self.assertEqual(reclass_a(0.001), 2)
        self.assertEqual(reclass_a(5.0), 2)
        self.assertEqual(reclass_a(5.001), 3)
        self.assertEqual(reclass_a(35.0), 8)
        self.assertEqual(reclass_a(35.001), 9)
        self.assertEqual(reclass_a(40.0), 9)
        self.assertEqual(reclass_a(40.001), 0)  # Fuera de dominio

        # Reclass B: Cortes [2, 4, 6, 8, 10, 12, 15, 20, 25]
        self.assertEqual(reclass_b(1.5), 1)
        self.assertEqual(reclass_b(2.0), 1)
        self.assertEqual(reclass_b(2.001), 2)
        self.assertEqual(reclass_b(25.0), 9)
        self.assertEqual(reclass_b(25.001), 10)

        # Reclass C: Millares [2000..17000]
        self.assertEqual(reclass_c(1.9), 2000)
        self.assertEqual(reclass_c(2.0), 2000)
        self.assertEqual(reclass_c(2.001), 3000)
        self.assertEqual(reclass_c(4.0), 4000)
        self.assertEqual(reclass_c(4.001), 5000)
        self.assertEqual(reclass_c(16.0), 16000)
        self.assertEqual(reclass_c(16.001), 17000)
        self.assertEqual(reclass_c(30.0), 17000)
        self.assertEqual(reclass_c(30.001), 0)  # Fuera de dominio

        # Reclass E: Viento cortes [3, 5, 10, 15, 20, 25, 30]
        self.assertEqual(reclass_e(2.5), 1)
        self.assertEqual(reclass_e(3.0), 1)
        self.assertEqual(reclass_e(3.001), 2)
        self.assertEqual(reclass_e(19.999), 5)
        self.assertEqual(reclass_e(20.0), 5)
        self.assertEqual(reclass_e(20.001), 6)
        self.assertEqual(reclass_e(30.0), 7)
        self.assertEqual(reclass_e(30.001), 8)

        # Reclass F: Binario 20 km/h
        self.assertEqual(reclass_f(19.999), 0)
        self.assertEqual(reclass_f(20.000), 1)
        self.assertEqual(reclass_f(20.001), 1)

        # Reclass G: Hillshade 123.5
        self.assertEqual(reclass_g(0.0), 200)      # Sombreado
        self.assertEqual(reclass_g(123.500), 200)  # Sombreado
        self.assertEqual(reclass_g(123.501), 100)  # Expuesto
        self.assertEqual(reclass_g(255.0), 100)    # Expuesto

    def test_composite_key_formation(self) -> None:
        """Verifica la generación de la Clave Compuesta de 288 combinaciones."""
        # Caso: HCFM=4.5 % (C=5000), Hillshade=200 (G=100 Expuesto), Temp=32 °C (A=8)
        # Clave esperada = 5000 + 100 + 8 = 5108
        clave = clave_pi(4.5, 32.0, 200.0)
        self.assertEqual(clave, 5108)

        # Caso sombreado (Hillshade=50 -> G=200): 5000 + 200 + 8 = 5208
        clave_sombra = clave_pi(4.5, 32.0, 50.0)
        self.assertEqual(clave_sombra, 5208)

        # Caso fuera de dominio térmico (T=42 °C -> A=0 -> Clave=0)
        clave_extrema = clave_pi(4.5, 42.0, 200.0)
        self.assertEqual(clave_extrema, 0)

    def test_pi_matrix_dimension_and_lookup(self) -> None:
        """Verifica que la matriz Rothermel tenga exactamente 288 celdas y que la consulta funcione."""
        self.assertEqual(len(MATRIZ_PI_ROTHERMEL), 288)

        # Consultar clave 5108 (debe ser un valor float entre 0 y 100)
        val_pi = probabilidad_ignicion(32.0, 17.0, 200.0)
        self.assertIsInstance(val_pi, float)
        self.assertGreaterEqual(val_pi, 0.0)
        self.assertLessEqual(val_pi, 100.0)

    def test_nwcg_table_fidelity_error(self) -> None:
        """Verifica que la reconstrucción Rothermel reproduzca la tabla oficial NWCG con MAE < 1.0 pp."""
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

        mae = sum(errores) / len(errores)
        self.assertLess(mae, 1.0)
        self.assertAlmostEqual(mae, 0.833333, places=2)

    def test_hourly_activation_rule(self) -> None:
        """Verifica la conjunción estricta (PI >= 70) AND (Viento >= 20)."""
        # 1. PI suficiente, viento insuficiente
        self.assertFalse(condicion_boton_rojo(80.0, 19.999))

        # 2. Viento suficiente, PI insuficiente
        self.assertFalse(condicion_boton_rojo(69.99, 25.0))

        # 3. Exactamente ambos umbrales
        self.assertTrue(condicion_boton_rojo(70.0, 20.0))

        # 4. Ambos superados ampliamente
        self.assertTrue(condicion_boton_rojo(85.0, 35.0))

    def test_daily_accumulation_and_fuels(self) -> None:
        """Verifica la acumulación de 1 a 5 horas y la máscara de combustible."""
        # 5 pasos horarios para 3 píxeles
        condiciones = np.array([
            [True,  False, True],
            [True,  True,  False],
            [True,  True,  True],
            [False, True,  True],
            [True,  True,  True]
        ])
        horas = horas_boton_rojo(condiciones)
        np.testing.assert_array_equal(horas, np.array([4, 4, 4]))

        # Máscara WorldCover (clases 10, 20, 30, 40, 90 son True; 50, 60, 70, 80 son False)
        coberturas = np.array([10, 20, 50, 60, 30, 40, 90, 80])
        mask = mascara_combustible(coberturas)
        esperado = np.array([True, True, False, False, True, True, True, False])
        np.testing.assert_array_equal(mask, esperado)

    def test_commune_zonal_reduction(self) -> None:
        """Verifica la reducción zonal comunal, com_ha y proportion."""
        # Raster 2x2:
        # Píxel (0,0): Comuna 1, 25 ha, Combustible, 3 horas BR
        # Píxel (0,1): Comuna 1, 25 ha, Combustible, 3 horas BR
        # Píxel (1,0): Comuna 1, 25 ha, NO combustible, 0 horas BR
        # Píxel (1,1): Comuna 2, 25 ha, Combustible, 5 horas BR
        horas_dia = {"2026-01-15": np.array([[3, 3], [0, 5]], dtype=np.int16)}
        raster_comunas = np.array([[1, 1], [1, 2]], dtype=np.int32)
        raster_area_ha = np.full((2, 2), 25.0)
        mascara_comb = np.array([[True, True], [False, True]])

        dict_comunas = {
            1: {"com_id": "13101", "com": "Santiago", "prov": "Santiago", "reg": "Metropolitana"},
            2: {"com_id": "13102", "com": "Providencia", "prov": "Santiago", "reg": "Metropolitana"}
        }

        df = reducir_comunal(
            horas_por_dia=horas_dia,
            raster_comunas=raster_comunas,
            raster_area_ha=raster_area_ha,
            mascara_comb=mascara_comb,
            dict_comunas=dict_comunas
        )

        self.assertEqual(len(df), 2)

        # Comuna 1 (Santiago): 2 píxeles con 3 horas = 50 ha; com_ha = 50 ha; proportion = 1.0
        fila1 = df[df["com_id"] == "13101"].iloc[0]
        self.assertEqual(fila1["horas"], 3)
        self.assertEqual(fila1["SUM_br_ha"], 50.0)
        self.assertEqual(fila1["com_ha"], 50.0)
        self.assertEqual(fila1["proportion"], 1.0)

        # Comuna 2 (Providencia): 1 píxel con 5 horas = 25 ha; com_ha = 25 ha; proportion = 1.0
        fila2 = df[df["com_id"] == "13102"].iloc[0]
        self.assertEqual(fila2["horas"], 5)
        self.assertEqual(fila2["SUM_br_ha"], 25.0)
        self.assertEqual(fila2["com_ha"], 25.0)
        self.assertEqual(fila2["proportion"], 1.0)


if __name__ == "__main__":
    unittest.main()
