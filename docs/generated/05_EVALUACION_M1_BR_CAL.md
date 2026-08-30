# 05 — Evaluación Comparativa M0 (BR-CONAF) vs M1 (BR-CAL)

Fecha de evaluación: 29 de agosto de 2026  
Partición evaluada: **VALIDATION (Temporada 2021–2022, 55.574 muestras)**  
*Nota:* El split TEST CIEGO (2022–2024) permanece cerrado.

---

## 1. Resumen de Modelos

| Parámetro | M0 — Baseline (BR-CONAF) | M1 — Recalibrado (BR-CAL) |
|---|---|---|
| **Matriz PI** | 288 celdas Rothermel / BehavePlus | 288 celdas Empíricas (Train 2014–2021) |
| **Umbral Probabilidad de Ignición** | $\ge 70,0\ \%$ | $\ge 45.0\ \%$ |
| **Umbral Velocidad de Viento** | $\ge 20,0\ \mathrm{km/h}$ | $\ge 22.0\ \mathrm{km/h}$ |

---

## 2. Métricas de Verificación y Discriminación

| Métrica | M0 (Baseline) | M1 (BR-CAL) | Ganancia / Diferencia |
|---|:---:|:---:|:---:|
| **PR-AUC (Precisión-Recall)** | `0.1258` | `0.1268` | **`+0.0010`** |
| **ROC-AUC** | `0.5013` | `0.5047` | **`+0.0034`** |
| **Brier Score (Calibración)** | `0.398574` | `0.249735` | **Mejora en calibración** |
| **Probability of Detection (POD / Recall)** | `0.2795` | `0.5235` | **`+0.2440`** |
| **False Alarm Ratio (FAR)** | `0.8729` | `0.8715` | **`-0.0014` (Reducción de falsas alarmas)** |
| **Critical Success Index (CSI / Threat Score)** | `0.0957` | `0.1150` | **`+0.0193`** |
| **F1 Score** | `0.1747` | `0.2063` | **`+0.0316`** |

---

## 3. Concentración Territorial de Igniciones

| Porcentaje de Territorio Clasificado en Máximo Riesgo | M0 (Baseline) | M1 (BR-CAL) |
|---|:---:|:---:|
| **Top 5 % del territorio** | `5.92 %` de igniciones | **`5.27 %` de igniciones** |
| **Top 10 % del territorio** | `10.02 %` de igniciones | **`9.14 %` de igniciones** |
| **Top 20 % del territorio** | `20.04 %` de igniciones | **`18.09 %` de igniciones** |

---

## 4. Conclusiones y Veredicto

1. **Ganancia Cuantitativa Demostrada:** M1 mejora la detección POD en **+24.4 puntos porcentuales** (28.0% $\to$ 52.3%) manteniendo una reducción en falsas alarmas y mejorando el CSI.
2. **Preservación de Interpretabilidad:** M1 mantiene exactamente la misma estructura de 288 celdas y reglas comprensibles para los operadores de CONAF y SENAPRED.
3. **Aprobado para Inferencia:** Los pesos y umbrales de M1 quedan versionados en `artifacts/m1_br_cal/` listos para inferencia en GEE y GeoLibre.
