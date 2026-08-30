# 03 — Matriz de Gaps, Riesgos y Mitigaciones

Fecha de evaluación: 29 de agosto de 2026  
Módulo: BR-HR — Evaluación Integral de Riesgos y Gaps del Sistema  
Responsables: Fire Science Reviewer, Geospatial Architect, Data Scientist, Backend Engineer, QA Engineer

---

## 1. Gaps Metodológicos y Científicos

| ID | Gap Identificado | Impacto en el Sistema | Mitigación en BR-HR |
|---|---|---|---|
| **GAP-01** | **Matriz PI de CONAF no publicada** | La réplica con la fórmula teórica de Rothermel es excesivamente restrictiva ($\mathrm{HR} \le 15\%$). | 1. Congelar M0 con matriz Rothermel como referencia teórica.<br>2. Cosechar / invertir empíricamente capas PI publicadas por CONAF.<br>3. Desarrollar **BR-CAL (M1)** recalculando la probabilidad empírica sobre los 68k eventos reales. |
| **GAP-02** | **HCFM sin memoria temporal ni balance hídrico** | La fórmula actual es una regresión instantánea; ignora lluvias previas, déficit de presión de vapor acumulado y sequedad de combustible vivo. | Incorporar en features de M2: lluvia acumulada (1h, 24h, 72h, 7d), VPD, radiación solar neta y humedad del suelo (ERA5-Land / GFS). |
| **GAP-03** | **Ausencia de factor humano en la ignición** | Más del 95 % de los incendios chilenos son antrópicos; el modelo meteorológico puro genera falsas alarmas en zonas remotas deshabitadas. | Incorporar capas estáticas de accesibilidad: distancia a red vial, proximidad a centros poblados e interfaz urbano-rural (WUI), respetando temporalidad estricta. |
| **GAP-04** | **Falsa resolución meteorológica (Resampling vs Downscaling)** | El remuestreo de GFS (25 km $\to$ 2 km) en el legado es mera interpolación bilineal sin física topográfica. | Implementar downscaling físico auditable en GEE: corrección de temperatura por gradiente altotérmico (lapse rate) y DEM de 30 m, humedad termodinámicamente coherente y factor de rugosidad/exposición topográfica para viento. |
| **GAP-05** | **Ausencia de validación estadística formal del baseline** | CONAF nunca ha publicado métricas de verificación (POD, FAR, CSI, PR-AUC) para Botón Rojo. | Establecer el primer benchmark formal de desempeño retrospectivo sobre las 10 temporadas históricas (2014–2024). |

---

## 2. Riesgos de Data Science y Modelado

| ID | Riesgo | Probabilidad / Severidad | Estrategia de Mitigación y Control |
|---|---|---|---|
| **RSK-01** | **Data Leakage temporal en features de ignición** | Media / **Crítica** | 1. Implementar regla dura `available_at <= prediction_time`.<br>2. Prohibir en $P(\mathrm{IGN})$ variables de superficie final, tiempos de combate o causa.<br>3. Cálculo de historial de incendios estrictamente hacia el pasado ($t' < t$).<br>4. Tests unitarios automáticos anti-leakage en el pipeline. |
| **RSK-02** | **Contaminación del Test Ciego (2022–2024)** | Media / **Crítica** | 1. Congelar las temporadas 2022–23 y 2023–24 en un split ciego cerrado.<br>2. Prohibir su uso para selección de variables, tuning o calibración.<br>3. Abrir el test una sola vez al finalizar el desarrollo para el reporte final. |
| **RSK-03** | **Distorsión de probabilidades por muestreo Case-Control** | Alta / **Alta** | 1. El ratio de muestreo (p.ej. 10 controles espaciales y 5 temporales por positivo) altera la prevalencia artificialmente.<br>2. Registrar explícitamente `sample_weight` e `inclusion_probability`.<br>3. Aplicar calibración posterior (Platt / Isotonic / Beta) sobre universo representativo de riesgo para publicar verdaderas probabilidades absolutas. |
| **RSK-04** | **Sobreajuste espacial (Overfitting regional)** | Media / **Alta** | Realizar validación cruzada espacial (*Leave-One-Region-Out* y bloques espaciales) además de la validación temporal. |
| **RSK-05** | **Confusión entre Probabilidad ($P$) y Confianza ($\mathrm{CONF}$)** | Alta / **Media** | Separar conceptualmente y en contratos de API: $P(\mathrm{IGN})$ es la probabilidad del evento; $\mathrm{CONF}$ es la certeza del dato (dependiente del horizonte forecast D+1..D+5, cobertura observacional y dispersión). |

---

## 3. Riesgos de Arquitectura y Rendimiento

| ID | Riesgo | Probabilidad / Severidad | Estrategia de Mitigación y Control |
|---|---|---|---|
| **RSK-06** | **Cuellos de botella en `reduceRegions` nacional en GEE** | Alta / **Alta** | 1. No ejecutar `reduceRegions` sobre geometrías vectoriales complejas en cada request.<br>2. Precomputar geometrías H3 estáticas en asset GEE.<br>3. Servir geometrías vía PMTiles estáticos en Cloudflare R2.<br>4. Railway API consulta atributos precomputados o raster tiles de Earth Engine REST. |
| **RSK-07** | **Sobre-ingeniería por introducción de PostGIS innecesario** | Alta / **Media** | Mantener la regla no negociable: **PostgreSQL/PostGIS no es parte del MVP**. Se utiliza R2 para almacenamiento de Parquet/PMTiles/JSON y Railway como API stateless ligera. |
| **RSK-08** | **Exposición de credenciales de Google Earth Engine / GCP / R2** | Baja / **Crítica** | 1. Frontend (GeoLibre) nunca interactúa directamente con Earth Engine ni posee claves privadas.<br>2. Railway autentica server-side mediante Service Account / ADC.<br>3. Toda credencial vive en variables de entorno seguras fuera del repositorio Git. |
| **RSK-09** | **Desfase horario y transiciones DST en Chile** | Media / **Media** | Eliminar cualquier offset estático (`-4`). Utilizar manejo estricto de zona horaria con IANA `America/Santiago` para etiquetar correctamente cada paso horario en UTC y hora local. |

---

## 4. Matriz de Decisión: Trade-offs del MVP

```text
┌──────────────────────────────┬──────────────────────────────┐
│       EVITAR EN EL MVP       │       PRIORIZAR EN EL MVP    │
├──────────────────────────────┼──────────────────────────────┤
│ • Modelos físicos 3D         │ • Regresión logística / GAM  │
│ • PostGIS / pygeoapi pesado  │ • H3-8 estático + R2 PMTiles │
│ • Interpolación ciega 250m   │ • Downscaling físico básico  │
│ • WindNinja en cada corrida  │ • Modelo champion interprete │
│ • Probabilidades sin calibrar│ • Calibración case-control   │
│ • Predicciones sin lineage   │ • Model card + run metadata  │
└──────────────────────────────┴──────────────────────────────┘
```
