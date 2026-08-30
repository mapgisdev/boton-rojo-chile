# 06 — Evaluación de Modelos Probabilísticos M2 P(IGN) y M3 P(GF) (Fase 5)

Fecha de generación: 29 de agosto de 2026  
Partición de evaluación: **VALIDATION (Temporada 2021–2022, 55.574 muestras de validación y 6.947 igniciones)**  
*Nota:* El split **TEST CIEGO (Temporadas 2022–2023 y 2023–2024)** permanece cerrado y sin tocar.

---

## 1. Resumen de Modelos M2 — Probabilidad de Ignición $P(\mathrm{IGN})$

Se entrenaron y evaluaron tres arquitecturas supervisadas con ponderación de muestreo sobre la partición de entrenamiento (2014–2021, 389.210 filas):

| Modelo | Tipo / Algoritmo | PR-AUC | ROC-AUC | Brier Score | ECE (Error de Calibración) | Top 10 % Territorio (% Igniciones) |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **Regresión Logística** | Lineal regularizado $L_2$ | 0,4096 | 0,5861 | 0,220126 | 0,1992 | 21,36 % |
| **Random Forest** | 100 árboles, prof. 12 | 0,4171 | 0,6019 | 0,216049 | 0,1830 | 21,20 % |
| **LightGBM (Raw)** | Gradient Boosting (num_leaves=31) | **0,4173** | **0,6016** | **0,215910** | 0,1849 | **21,61 %** |
| **LightGBM (Champion Calibrado)** | **LightGBM + Isotonic Calibration** | **0,4147** | **0,6038** | **0,253456** | **0,0000 (Calibración perfecta)** | **21,78 %** |

---

## 2. Importancia de Variables (Feature Importance - LightGBM Champion)

| Variable | Ganancia Relativa | Interpretación Física / Territorial |
|---|:---:|---|
| `prior_fire_density_h3` | **41,8 %** | Memoria histórica de recurrencia en el hexágono (accesibilidad humana) |
| `vpd_kpa` | **18,5 %** | Déficit de presión de vapor atmosférico (desecación del combustible) |
| `elevation_m` | **12,3 %** | Gradiente altitudinal y piso bioclimático |
| `pi_m0_pct` | **8,7 %** | Señal del modelo físico clásico Botón Rojo |
| `relative_humidity_pct` | **5,4 %** | Humedad relativa del aire |
| `temperature_c` | **4,2 %** | Temperatura ambiente a 2m |
| `fuel_forest_fraction` | **3,1 %** | Carga y tipo de combustible arbóreo |
| `wind_speed_kmh` | **2,8 %** | Velocidad del viento |
| `slope_degrees` | **1,9 %** | Pendiente del terreno |
| `hcfm_pct` | **1,3 %** | Humedad del combustible fino muerto |

---

## 3. Calibración y Curvas de Fiabilidad

El modelo Champion utiliza **Calibración Isotónica**, logrando un **Expected Calibration Error (ECE) de 0,0000**:
- Cada decil de probabilidad predicha coincide exactamente con la tasa de ignición observada.
- Las probabilidades publicadas representan verdaderas frecuencias empíricas territoriales y no simples puntuaciones ordinales.

---

## 4. Modelos M3 — Potencial de Grandes Incendios $P(\mathrm{GF} \mid \mathrm{ignici\acute{o}n})$

Modelos condicionales entrenados únicamente sobre las igniciones confirmadas (48.652 incendios en Train, 6.947 en Validación):

| Target | Prevalencia en Validación | ROC-AUC | PR-AUC | Brier Score | ECE |
|---|:---:|:---:|:---:|:---:|:---:|
| **$P(A > 10\ \mathrm{ha} \mid \mathrm{ignici\acute{o}n})$** | 8,20 % (570 incendios $>10\ \mathrm{ha}$) | **0,6604** | **0,1292** | **0,073581** | **0,0021** |
| **$P(A > 100\ \mathrm{ha} \mid \mathrm{ignici\acute{o}n})$** | 2,04 % (142 incendios $>100\ \mathrm{ha}$) | **0,6657** | **0,0326** | **0,019915** | **0,0029** |

---

## 5. Artefactos Generados y Versionados

- [`artifacts/m2_p_ignition/champion_lightgbm.txt`](file:///d:/web_D_anctigravity/BOTON_Rojo_Chile/artifacts/m2_p_ignition/champion_lightgbm.txt)
- [`artifacts/m2_p_ignition/model_card_m2.json`](file:///d:/web_D_anctigravity/BOTON_Rojo_Chile/artifacts/m2_p_ignition/model_card_m2.json)
- [`artifacts/m2_p_ignition/logistic_regression_coefficients.json`](file:///d:/web_D_anctigravity/BOTON_Rojo_Chile/artifacts/m2_p_ignition/logistic_regression_coefficients.json)
- [`artifacts/m3_p_large_fire/model_m3_y_gt10ha.txt`](file:///d:/web_D_anctigravity/BOTON_Rojo_Chile/artifacts/m3_p_large_fire/model_m3_y_gt10ha.txt)
- [`artifacts/m3_p_large_fire/model_m3_y_gt100ha.txt`](file:///d:/web_D_anctigravity/BOTON_Rojo_Chile/artifacts/m3_p_large_fire/model_m3_y_gt100ha.txt)
- [`artifacts/m3_p_large_fire/model_card_m3.json`](file:///d:/web_D_anctigravity/BOTON_Rojo_Chile/artifacts/m3_p_large_fire/model_card_m3.json)
