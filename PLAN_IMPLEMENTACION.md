# Plan de Implementación BR-HR (Botón Rojo de Alta Resolución)

**Versión:** 1.0  
**Fecha:** 29 de agosto de 2026  
**Estado:** Propuesta técnica completa para revisión y aprobación  
**Autores/Roles:** Principal Geospatial Architect, Spatial Data Scientist, Fire Science Specialist, Backend & QA Engineers

---

## 1. Visión y Objetivos

El proyecto **BR-HR** desarrolla un sistema territorial probabilístico, continuo y auditable para el peligro y potencial de incendios forestales en Chile. Preserva el sistema **Botón Rojo original** como baseline institucional inmutable (M0), al tiempo que introduce:
1. **BR-CAL (M1):** Recalibración empírica transparente de la matriz de ignición y umbrales con observaciones 2014–2024.
2. **P-IGN (M2):** Modelo probabilístico calibrado de ignición por celda H3 resolución 8 (~74 ha) y por hora ($P(\mathrm{ignici\acute{o}n}_{h,t})$).
3. **P-GF (M3):** Modelo condicional de potencial de propagación ($P(A > 10\ \mathrm{ha} \mid \mathrm{ignici\acute{o}n})$ y $P(A > 100\ \mathrm{ha} \mid \mathrm{ignici\acute{o}n})$).
4. **Arquitectura Ligera:** Motor geoespacial en Google Earth Engine, API stateless en Railway, almacenamiento estático en Cloudflare R2 (PMTiles/Parquet/JSON) y visualización en GeoLibre / MapLibre, sin dependencias pesadas de bases de datos espaciales en el MVP.

---

## 2. Estructura del Repositorio Propuesta

```text
BOTON_Rojo_Chile/
├── GEMINI.md
├── AGENTS.md
├── PLAN_IMPLEMENTACION.md
├── .antigravity/
│   └── rules.md
├── docs/
│   ├── 01_VISION_Y_ALCANCE.md
│   ├── 02_METODOLOGIA_CIENTIFICA.md
│   ├── 03_BLUEPRINT_TECNICO.md
│   ├── 04_DATASET_MAESTRO.md
│   ├── 05_PLAN_DE_DESARROLLO.md
│   ├── 06_CONTRATO_API.md
│   ├── 07_ARQUITECTURA_EARTH_ENGINE.md
│   ├── 08_VALIDACION_QAQC.md
│   ├── 09_DECISIONES_NO_NEGOCIABLES.md
│   ├── 10_REFERENCIAS_TECNICAS.md
│   └── generated/
│       ├── 00_INVENTARIO_INSUMOS.md
│       ├── 01_AUDITORIA_LEGACY.md
│       ├── 02_PERFIL_DATOS_INCENDIOS.md
│       ├── 03_GAPS_Y_RIESGOS.md
│       └── DECISION_LOG.md
├── insumos/                               [SOLO LECTURA INMUTABLE]
│   ├── Boton_Rojo.zip
│   └── Consolidado_incendios_2014_2024_temporada.csv
├── data/
│   ├── raw/
│   ├── derived/
│   │   ├── incendios_qa.parquet
│   │   ├── h3_chile_r8_index.parquet
│   │   ├── h3_commune_weights.parquet
│   │   └── master_fire_h3/
│   └── schemas/
├── src/
│   ├── baseline/                          # M0 — BR-CONAF
│   │   ├── __init__.py
│   │   ├── conaf_core.py                  # Algoritmo puro con correcciones técnicas seguras
│   │   ├── pi_matrix.py                   # Matriz Rothermel / NWCG 288 celdas
│   │   └── tables.py                      # Reclass A-G
│   ├── training/                          # Ciencia de datos y pipelines
│   │   ├── qa/
│   │   │   ├── dataset_cleaner.py         # Parsing temporal IANA, QA coords, flags
│   │   │   └── leakage_checker.py         # Validador automático anti-leakage
│   │   ├── sampling/
│   │   │   ├── case_control.py            # Generador de controles espaciales y temporales
│   │   │   └── universe_at_risk.py        # Filtro de dominios no combustibles
│   │   ├── features/
│   │   │   ├── builder.py                 # Extracción y ensamblaje de covariables
│   │   │   ├── terrain.py                 # DEM 30m, pendientes, aspecto, exposición
│   │   │   ├── fuels.py                   # Fracciones MapBiomas por año
│   │   │   ├── human.py                   # Proximidad a vías y centros poblados
│   │   │   └── memory.py                  # Precipitación acumulada, VPD, sequedad
│   │   ├── models/
│   │   │   ├── br_calibrated.py           # M1: BR-CAL (Matriz empírica y umbrales)
│   │   │   ├── p_ignition.py              # M2: Logistic, GAM, RF, LightGBM
│   │   │   ├── p_large_fire.py            # M3: Modelos condicionales >10ha, >100ha
│   │   │   └── calibrator.py              # Platt, Isotonic, Beta Calibration
│   │   └── validation/
│   │       ├── metrics.py                 # PR-AUC, ROC-AUC, Brier, POD, FAR, CSI
│   │       ├── spatial_cv.py              # Leave-One-Region-Out, spatial blocks
│   │       └── backtest.py                # GFS D+1..D+5 evaluation
│   ├── gee/                               # Módulos Earth Engine JavaScript / Python
│   │   ├── config.py
│   │   ├── baseline_module.js             # M0 en GEE sin errores de resampling
│   │   ├── downscaling_module.js          # Lapse-rate T, humedad coherente, viento
│   │   ├── inference_module.js            # Modelo champion operacional en GEE
│   │   └── h3_rollup.js                   # Agregación H3-8 y comunal
│   ├── api/                               # Backend Railway
│   │   ├── main.py                        # FastAPI entrypoint
│   │   ├── routers/
│   │   │   ├── health.py
│   │   │   ├── runs.py
│   │   │   ├── hex.py
│   │   │   └── communes.py
│   │   ├── services/
│   │   │   ├── gee_auth.py                # Autenticación segura Service Account / REST
│   │   │   └── r2_client.py               # Consulta de Parquet / JSON en Cloudflare R2
│   │   └── schemas/                       # Pydantic v2 schemas
│   └── shared/
│       ├── config.py
│       ├── logging.py
│       └── time_utils.py                  # Utilidades IANA America/Santiago / UTC
├── tests/
│   ├── unit/
│   │   ├── test_baseline_golden.py        # Fixtures de regresión estricta M0
│   │   ├── test_time_conversions.py
│   │   └── test_leakage_invariants.py
│   ├── integration/
│   │   ├── test_gee_parity.py             # Verificación cruzada Python vs GEE
│   │   └── test_api_contracts.py
│   └── acceptance/
│       └── test_blind_test_evaluation.py
├── artifacts/                             # Model cards, pesos, métricas congeladas
├── work/                                  # Extracciones y scratch local
└── pyproject.toml
```

---

## 3. Plan de Desarrollo por Fases

| Fase | Título | Objetivos Principales | Archivos Clave | Pruebas / Aceptación | Complejidad |
|---|---|---|---|---|:---:|
| **Fase 0** | **Auditoría & Plan** *(Completada)* | Verificar insumos, auditar código legado, perfilar 68k incendios, mapear riesgos y definir roadmap. | `docs/generated/*`, `PLAN_IMPLEMENTACION.md` | Hashes SHA-256 verificados, 0 duplicados, perfil completo. | **S** |
| **Fase 1** | **Baseline Reproducible (M0 — BR-CONAF)** | Implementar réplica pura en Python y GEE, corregir defectos técnicos (resampling categórico, zona horaria dinámica, límites de dominio) sin alterar la metodología original. | `src/baseline/conaf_core.py`, `src/gee/baseline_module.js`, `tests/unit/test_baseline_golden.py` | 100 % coincidencia en golden fixtures; paridad Python $\leftrightarrow$ GEE. | **M** |
| **Fase 2** | **QA/QC Histórico & Geometría H3** | Estandarizar CSV histórico a Parquet con flags QA; generar índice espacial nacional H3-8 y matriz de intersección H3-Comuna (`h3_commune_weights.parquet`). | `src/training/qa/dataset_cleaner.py`, `data/derived/incendios_qa.parquet`, `data/derived/h3_commune_weights.parquet` | 68.538 eventos georreferenciados en H3; sumatoria de pesos comunales = 1.0 por hexágono. | **M** |
| **Fase 3** | **Dataset Maestro (`MASTER_FIRE_H3` v1)** | Generar pares caso-control (10 espaciales, 5 temporales en dominio combustible); extraer ERA5-Land, DEM 30m, MapBiomas anual y variables de proximidad humana. | `src/training/sampling/*`, `src/training/features/*`, `data/derived/master_fire_h3/` | Diccionario de datos versionado; 0 fallos en tests automáticos anti-leakage. | **L** |
| **Fase 4** | **Recalibración Botón Rojo (M1 — BR-CAL)** | Calcular matriz empírica de 288 celdas sobre el conjunto de entrenamiento (2014–2021); optimizar umbrales sobre el validation split (2021–22) sin tocar el test ciego. | `src/training/models/br_calibrated.py`, `artifacts/m1_br_cal/` | Demostrar ganancia estadística en PR-AUC y reducción de falsas alarmas frente a M0 en validación. | **M** |
| **Fase 5** | **Modelos Probabilísticos (M2 P-IGN y M3 P-GF)** | Entrenar regresión logística, GAM, Random Forest y challenger LightGBM; aplicar calibración de probabilidades (Platt/Isotonic/Beta); entrenar modelos condicionales >10ha y >100ha. | `src/training/models/p_ignition.py`, `src/training/models/p_large_fire.py`, `src/training/models/calibrator.py` | Reliability curves con Brier Score minimizado; Model Cards documentadas; selección de champion. | **L** |
| **Fase 6** | **Evaluación del Test Ciego (2022–2024)** | Abrir una sola vez el split de test ciego (temporadas 2022-23 y 2023-24) para benchmark final inmutable de M0, M1, M2 y M3. | `tests/acceptance/test_blind_test_evaluation.py`, `docs/generated/04_REPORTE_TEST_CIEGO.md` | Reporte final congelado; verificación de generalización temporal sin tuning posterior. | **S** |
| **Fase 7** | **Backtest Operacional de Pronóstico** | Evaluar el modelo champion sobre pronósticos históricos NOAA GFS 0.25° para horizontes D+1 a D+5, midiendo degradación por horizonte. | `src/training/validation/backtest.py`, `artifacts/forecast_skill_curve.json` | Curva de habilidad por horizonte para parametrizar la capa de Confianza (`CONF`). | **M** |
| **Fase 8** | **Inferencia en Google Earth Engine** | Portar el modelo champion a GEE; generar raster ambiental 250 m con downscaling físico (lapse-rate T, humedad coherente, rugosidad de viento); rollup a H3-8 y comuna. | `src/gee/downscaling_module.js`, `src/gee/inference_module.js`, `src/gee/h3_rollup.js` | Paridad de inferencia GEE $\leftrightarrow$ Python ($|\Delta P| < 0.01$); export de map tiles optimizados. | **L** |
| **Fase 9** | **API Backend (Railway) & Storage (R2)** | Backend ligero FastAPI en Railway; orquestación server-side con GEE REST; endpoints de consulta H3 y comunal; publicación de Parquet/PMTiles en Cloudflare R2. | `src/api/*`, `templates/api_openapi_skeleton.yaml`, `infra/railway/` | Test de contratos OpenAPI aprobado; cero secretos expuestos; tiempos de respuesta $< 200\ \mathrm{ms}$. | **M** |
| **Fase 10** | **Integración GeoLibre / Frontend** | Mapas interactivos en GeoLibre / MapLibre; visualización de capas (M0, M1, P-IGN, P-GF, BR-FRAC, Viento, Confianza); selección H3 y serie temporal. | `src/frontend/` o especificación GeoLibre | Carga fluida a escala nacional; PMTiles servidos desde R2 sin transferir geometrías redundantes. | **M** |
| **Fase 11** | **Innovaciones de Alta Resolución** | Ablation studies incrementales: memoria dinámica de combustible ($FM_t$), estaciones meteorológicas DMC/INIA, piloto H3-9 (~10 ha), challenger WindNinja. | `src/training/features/advanced_*`, `docs/generated/ABLATION_STUDY.md` | Cada módulo nuevo debe demostrar ganancia cuantitativa fuera de muestra para ser promovido. | **L** |

---

## 4. Plan de Verificación y Criterios de Aceptación

### 4.1. Pruebas Automatizadas
1. **Regresión M0 (Golden Fixtures):** Vectores fijos de temperatura, humedad, viento y sombreado con salidas exactas esperadas.
2. **Invariantes Anti-Leakage:** Pruebas que fallan si cualquier feature en entrenamiento tiene `available_at > prediction_time`.
3. **Calibración Probabilística:** Validación de que las probabilidades predichas no superan un error de calibración esperado (ECE) prefijado.
4. **Contratos API:** Pruebas unitarias de esquemas Pydantic y respuestas JSON según especificación OpenAPI.

### 4.2. Criterios de Éxito Científico
- **M0 vs M1:** BR-CAL debe superar a BR-CONAF en PR-AUC y reducir falsas alarmas en el validation split.
- **M2 (P-IGN):** Mayor concentración territorial de incendios en el top 5 %, 10 % y 20 % del territorio respecto a los modelos heurísticos.
- **Calibración:** Curvas de confiabilidad alineadas con la diagonal en diagramas de fiabilidad.
- **Backtest Operacional:** Destreza predictiva estadísticamente significativa en horizontes D+1 y D+2.

---

## 5. Decisiones que Requieren Confirmación del Usuario

1. **Aprobación de la Fase 1:** Autorización para proceder con la implementación del Baseline M0 congelado (`src/baseline/`) y sus pruebas unitarias.
2. **Confirmación de Credenciales de Earth Engine:** Para la etapa de inferencia en GEE (Fase 8) y API (Fase 9), definir si se utilizará Service Account en GCP o Application Default Credentials (ADC).
3. **Confirmación de Nombres de Storage R2 / Railway:** Parámetros de entorno definitivos para buckets de Cloudflare R2 y variables de despliegue.
